from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import requests
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, text
from sqlalchemy.orm import Session
from .auth import admin, current_user, entitlement
from .config import settings
from .db import Base, engine, get_db
from .models import Expense, Income, Notification, Payment, Subscription
from .schemas import AllocationIn, CapitalIn, ExpenseIn, ExpenseOut, IncomeIn, NotificationOut, PricingIn, RecordOut, WhatsAppIn
from .services import BUSINESS_PLAN_SECTIONS, SWOT_SECTIONS, calculate_balance, calculate_capital_requirement, calculate_income_allocation, calculate_margin_price, calculate_markup_price, market_analysis, validate_swot

# The local SQLite fallback is used by the existing tests. The live Supabase
# schema is managed externally and must never be mutated on application start.
if engine.dialect.name == 'sqlite':
    Base.metadata.create_all(engine)
app = FastAPI(title='Techspot Financial Assistant API', version='1.0.0')

ADMIN_DIST = Path(__file__).resolve().parent.parent / 'admin' / 'dist'
if (ADMIN_DIST / 'assets').exists():
    app.mount('/assets', StaticFiles(directory=ADMIN_DIST / 'assets'), name='admin-assets')

@app.get('/')
def root():
    if (ADMIN_DIST / 'index.html').exists():
        return FileResponse(ADMIN_DIST / 'index.html')
    return {
        'service': 'Techspot Financial Assistant API',
        'status': 'healthy',
        'admin_dashboard': 'Run `cd admin; npm run dev` and open http://127.0.0.1:5173',
        'api_docs': '/docs',
    }

@app.get('/admin')
def admin_entry():
    if (ADMIN_DIST / 'index.html').exists():
        return FileResponse(ADMIN_DIST / 'index.html')
    return {
        'message': 'Admin frontend is not built in this environment.',
        'start_command': 'cd admin; npm run dev',
        'url': 'http://127.0.0.1:5173',
    }

@app.get('/health')
def health(): return {'status': 'healthy'}

def month_bounds(month: str):
    try: year, mon = map(int, month.split('-')); start = date(year, mon, 1); return start, date(year, mon, monthrange(year, mon)[1])
    except Exception: raise HTTPException(422, 'month must use YYYY-MM')

@app.post('/api/v1/income', response_model=RecordOut, dependencies=[Depends(entitlement('PLUS'))])
def add_income(payload: IncomeIn, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = Income(user_id=user_id, amount=payload.amount, entry_date=payload.entry_date); db.add(item); db.commit(); db.refresh(item); return item

@app.put('/api/v1/income/{item_id}', response_model=RecordOut, dependencies=[Depends(entitlement('PLUS'))])
def edit_income(item_id: int, payload: IncomeIn, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Income).filter_by(id=item_id, user_id=user_id, active=True).first()
    if not item: raise HTTPException(404, 'income not found')
    item.amount, item.entry_date = payload.amount, payload.entry_date; db.commit(); db.refresh(item); return item

@app.delete('/api/v1/income/{item_id}', dependencies=[Depends(entitlement('PLUS'))])
def delete_income(item_id: int, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Income).filter_by(id=item_id, user_id=user_id, active=True).first()
    if not item: raise HTTPException(404, 'income not found')
    item.active = False; db.commit(); return {'success': True}

@app.post('/api/v1/expenses', response_model=ExpenseOut, dependencies=[Depends(entitlement('PLUS'))])
def add_expense(payload: ExpenseIn, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = Expense(user_id=user_id, **payload.model_dump()); db.add(item); db.commit(); db.refresh(item); return item

@app.put('/api/v1/expenses/{item_id}', response_model=ExpenseOut, dependencies=[Depends(entitlement('PLUS'))])
def edit_expense(item_id: int, payload: ExpenseIn, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Expense).filter_by(id=item_id, user_id=user_id, active=True).first()
    if not item: raise HTTPException(404, 'expense not found')
    for k, v in payload.model_dump().items(): setattr(item, k, v)
    db.commit(); db.refresh(item); return item

@app.delete('/api/v1/expenses/{item_id}', dependencies=[Depends(entitlement('PLUS'))])
def delete_expense(item_id: int, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Expense).filter_by(id=item_id, user_id=user_id, active=True).first()
    if not item: raise HTTPException(404, 'expense not found')
    item.active = False; db.commit(); return {'success': True}

@app.get('/api/v1/budgets')
def budget(month: str = Query(...), user_id=Depends(entitlement('PLUS')), db: Session = Depends(get_db)):
    start, end = month_bounds(month)
    income = db.query(func.coalesce(func.sum(Income.amount), 0)).filter(Income.user_id == user_id, Income.active, Income.entry_date.between(start, end)).scalar()
    expenses = db.query(func.coalesce(func.sum(Expense.amount), 0)).filter(Expense.user_id == user_id, Expense.active, Expense.entry_date.between(start, end)).scalar()
    return calculate_balance(Decimal(income), Decimal(expenses)) | {'month': month}

@app.post('/api/v1/budgets/calculate')
def allocation(payload: AllocationIn, user_id=Depends(current_user)):
    try: return calculate_income_allocation(payload.monthly_income, payload.needs_percent, payload.investment_percent, payload.savings_percent)
    except ValueError as e: raise HTTPException(422, str(e))

@app.post('/api/v1/capital/calculate', dependencies=[Depends(entitlement('PREMIUM'))])
def capital(payload: CapitalIn): return calculate_capital_requirement(payload.costs, payload.assumptions)

@app.post('/api/v1/pricing/markup', dependencies=[Depends(entitlement('PREMIUM'))])
def markup(payload: PricingIn): return calculate_markup_price(payload.total_cost, payload.percentage)

@app.post('/api/v1/pricing/margin', dependencies=[Depends(entitlement('PREMIUM'))])
def margin(payload: PricingIn):
    try: return calculate_margin_price(payload.total_cost, payload.percentage)
    except ValueError as e: raise HTTPException(422, str(e))

@app.post('/api/v1/market-analysis', dependencies=[Depends(entitlement('PREMIUM'))])
def market(payload: dict): return market_analysis(payload.get('analysis', ''), payload.get('source'))

@app.post('/api/v1/business/swot', dependencies=[Depends(entitlement('PREMIUM'))])
def swot(payload: dict):
    try: return validate_swot(payload)
    except ValueError as e: raise HTTPException(422, str(e))

@app.get('/api/v1/business/plan/sections', dependencies=[Depends(entitlement('PREMIUM'))])
def business_plan_sections(): return {'required_sections': list(BUSINESS_PLAN_SECTIONS)}

@app.get('/api/v1/notifications', response_model=list[NotificationOut])
def notifications(user_id=Depends(current_user), db: Session = Depends(get_db)): return db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

@app.patch('/api/v1/notifications/{item_id}/read')
def read_notification(item_id: int, user_id=Depends(current_user), db: Session = Depends(get_db)):
    item = db.query(Notification).filter_by(id=item_id, user_id=user_id).first()
    if not item: raise HTTPException(404, 'notification not found')
    item.read = True; db.commit(); return {'success': True}

@app.post('/api/v1/webhooks/payment')
def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    event_id = payload.get('event_id'); user_id = payload.get('user_id'); tier = payload.get('tier', 'FREE')
    if not event_id or not user_id or tier not in {'PLUS', 'PREMIUM'}: raise HTTPException(422, 'invalid payment event')
    if db.query(Payment).filter_by(provider_event_id=event_id).first(): return {'success': True, 'duplicate': True}
    db.add(Payment(provider_event_id=event_id, user_id=user_id, tier=tier, status='verified'))
    sub = db.query(Subscription).filter_by(user_id=user_id).first()
    if sub: sub.tier, sub.active = tier, True
    else: db.add(Subscription(user_id=user_id, tier=tier, active=True))
    db.commit(); return {'success': True, 'duplicate': False}

@app.post('/api/v1/whatsapp/message')
def whatsapp(payload: WhatsAppIn): return {'success': True, 'response': 'Mensagem recebida. O processamento está pronto para integração com n8n.', 'data': {}, 'session_id': payload.session_id, 'error': None}

@app.get('/api/v1/admin/payments', dependencies=[Depends(admin)])
def admin_payments(db: Session = Depends(get_db)): return [{'id': p.id, 'user_id': p.user_id, 'tier': p.tier, 'status': p.status} for p in db.query(Payment).all()]

@app.get('/api/v1/admin/dashboard', dependencies=[Depends(admin)])
def admin_dashboard(db: Session = Depends(get_db)):
    """Return admin metrics from the tables that actually exist in this deployment.

    Missing ERD tables are represented as unavailable rather than estimated.
    """
    if engine.dialect.name == 'postgresql':
        return _postgres_admin_dashboard(db)

    subscription_counts = {
        tier: db.query(func.count(Subscription.id)).filter(Subscription.tier == tier).scalar() or 0
        for tier in ('FREE', 'PLUS', 'PREMIUM')
    }
    payment_counts = {
        status: db.query(func.count(Payment.id)).filter(Payment.status == status).scalar() or 0
        for status in ('initiated', 'pending', 'success', 'verified', 'failed', 'cancelled', 'refunded')
    }
    notification_total = db.query(func.count(Notification.id)).scalar() or 0
    notification_read = db.query(func.count(Notification.id)).filter(Notification.read.is_(True)).scalar() or 0
    return {
        'source': 'current_database_schema',
        'metrics': {
            'users': {'total': None, 'active': None, 'new_registrations': None, 'available': False},
            'subscriptions': {
                'free': subscription_counts['FREE'], 'plus': subscription_counts['PLUS'],
                'premium': subscription_counts['PREMIUM'], 'active': db.query(func.count(Subscription.id)).filter(Subscription.active.is_(True)).scalar() or 0,
                'expired': None, 'cancelled': None, 'available': True,
            },
            'payments': {
                'total': db.query(func.count(Payment.id)).scalar() or 0,
                'by_status': payment_counts,
                'verified': payment_counts['verified'] + payment_counts['success'],
                'revenue': None,
                'available': True,
            },
            'notifications': {
                'total': notification_total, 'read': notification_read,
                'unread': notification_total - notification_read, 'available': True,
            },
            'business': {'available': False},
            'ai': {'available': False},
            'audit_logs': {'available': False},
            'privacy': {'available': False},
        },
        'recent_activity': [],
    }

@app.post('/api/v1/admin/setup-password')
def setup_admin_password(payload: dict, db: Session = Depends(get_db)):
    email = str(payload.get('email', '')).strip().lower()
    password = str(payload.get('password', ''))
    confirmation = str(payload.get('confirmation', ''))
    if not email or len(password) < 8 or password != confirmation:
        raise HTTPException(422, 'email, matching passwords of at least 8 characters are required')
    if engine.dialect.name != 'postgresql': raise HTTPException(503, 'Supabase Auth is unavailable')
    auth_user_id = db.execute(text('select id from auth.users where lower(email)=:email and deleted_at is null'), {'email': email}).scalar()
    if not auth_user_id: raise HTTPException(404, 'admin account not found')
    allowed = db.execute(text("select exists (select 1 from public.admin_users au join public.admin_roles ar on ar.role_id=au.admin_role_id where au.auth_user_id=:uid and upper(au.status)='ACTIVE' and upper(ar.role_name)='SUPER_ADMIN')"), {'uid': auth_user_id}).scalar()
    if not allowed: raise HTTPException(403, 'Super Admin mapping required')
    response = requests.put(settings.supabase_url.rstrip('/') + f'/auth/v1/admin/users/{auth_user_id}', headers={'apikey': settings.supabase_service_role_key, 'Authorization': f'Bearer {settings.supabase_service_role_key}', 'Content-Type': 'application/json'}, json={'password': password}, timeout=10)
    if response.status_code >= 300: raise HTTPException(502, 'password update failed')
    return {'success': True, 'message': 'Password set. You can now sign in.'}

def _postgres_admin_dashboard(db: Session):
    def scalar(sql, params=None):
        return db.execute(text(sql), params or {}).scalar() or 0

    subscription_counts = dict(db.execute(text("""
        select upper(coalesce(sp.plan_code, 'UNKNOWN')), count(*)
        from public.user_subscriptions us
        left join public.subscription_plans sp on sp.plan_id = us.plan_id
        group by 1
    """)).fetchall())
    status_counts = dict(db.execute(text("""
        select upper(coalesce(payment_status, 'UNKNOWN')), count(*)
        from public.payments group by 1
    """)).fetchall())
    return {
        'source': 'supabase.public',
        'metrics': {
            'users': {
                'total': scalar('select count(*) from public.users'),
                'active': scalar("select count(*) from public.users where upper(coalesce(account_status, '')) in ('ACTIVE','ENABLED')"),
                'new_registrations': scalar("select count(*) from public.users where created_at >= date_trunc('month', now())"),
                'available': True,
            },
            'subscriptions': {
                'free': subscription_counts.get('FREE', 0),
                'plus': subscription_counts.get('PLUS', subscription_counts.get('BASIC', 0)),
                'premium': subscription_counts.get('PREMIUM', 0),
                'active': scalar("select count(*) from public.user_subscriptions where upper(coalesce(subscription_status,'')) = 'ACTIVE'"),
                'expired': scalar("select count(*) from public.user_subscriptions where upper(coalesce(subscription_status,'')) = 'EXPIRED'"),
                'cancelled': scalar("select count(*) from public.user_subscriptions where upper(coalesce(subscription_status,'')) in ('CANCELLED','CANCELED')"),
                'available': True,
            },
            'payments': {
                'total': scalar('select count(*) from public.payments'),
                'by_status': {k.lower(): v for k, v in status_counts.items()},
                'verified': sum(v for k, v in status_counts.items() if k in ('SUCCESS','VERIFIED','COMPLETED')),
                'revenue': scalar("select coalesce(sum(amount), 0) from public.payments where upper(coalesce(payment_status,'')) in ('SUCCESS','VERIFIED','COMPLETED')"),
                'available': True,
            },
            'notifications': {
                'total': scalar('select count(*) from public.user_notifications'),
                'read': scalar('select count(*) from public.user_notifications where is_read is true'),
                'unread': scalar('select count(*) from public.user_notifications where is_read is not true'),
                'available': True,
            },
            'business': {
                'profiles': scalar('select count(*) from public.business_profiles'),
                'plans': 0,
                'swot': scalar('select count(*) from public.swot_analyses'),
                'available': True,
            },
            'ai': {
                'conversations': scalar('select count(*) from public.ai_conversations'),
                'messages': scalar('select count(*) from public.ai_messages'),
                'available': True,
            },
            'audit_logs': {'available': False},
            'privacy': {'available': False},
        },
        'recent_activity': [],
    }

@app.get('/api/v1/admin/subscriptions', dependencies=[Depends(admin)])
def admin_subscriptions(db: Session = Depends(get_db)):
    if engine.dialect.name == 'postgresql':
        return [dict(row) for row in db.execute(text("""
            select us.subscription_id as id, us.user_id, sp.plan_code as tier,
                   us.subscription_status as status, us.payment_status,
                   us.start_date, us.end_date, us.created_at
            from public.user_subscriptions us
            left join public.subscription_plans sp on sp.plan_id = us.plan_id
            order by us.created_at desc nulls last, us.subscription_id desc
        """)).mappings().all()]
    return [
        {'id': s.id, 'user_id': s.user_id, 'tier': s.tier, 'active': s.active, 'expires_at': s.expires_at}
        for s in db.query(Subscription).order_by(Subscription.id.desc()).all()
    ]

@app.get('/api/v1/admin/notifications', dependencies=[Depends(admin)])
def admin_notifications(db: Session = Depends(get_db)):
    if engine.dialect.name == 'postgresql':
        return [dict(row) for row in db.execute(text("""
            select un.user_notification_id as id, un.user_id,
                   nt.title, nt.message, nt.notification_type,
                   un.is_read as read, un.sent_at, un.read_at
            from public.user_notifications un
            join public.notification_templates nt on nt.notification_id = un.notification_id
            order by un.sent_at desc nulls last, un.user_notification_id desc
        """)).mappings().all()]
    return [
        {'id': n.id, 'user_id': n.user_id, 'message': n.message, 'read': n.read, 'created_at': n.created_at}
        for n in db.query(Notification).order_by(Notification.created_at.desc()).all()
    ]

@app.get('/api/v1/admin/users', dependencies=[Depends(admin)])
def admin_users(db: Session = Depends(get_db)):
    if engine.dialect.name != 'postgresql': return []
    return [dict(row) for row in db.execute(text("""
        select u.user_id as id, coalesce(u.name, u.whatsapp_name, 'Unnamed user') as name,
               u.phone_number, u.city, u.account_status, u.created_at,
               coalesce(sp.plan_name, 'No subscription') as plan
        from public.users u
        left join lateral (
            select plan_id from public.user_subscriptions us
            where us.user_id = u.user_id order by us.created_at desc nulls last limit 1
        ) latest on true
        left join public.subscription_plans sp on sp.plan_id = latest.plan_id
        order by u.created_at desc nulls last, u.user_id desc
    """)).mappings().all()]

@app.get('/api/v1/admin/payments-live', dependencies=[Depends(admin)])
def admin_payments_live(db: Session = Depends(get_db)):
    if engine.dialect.name != 'postgresql': return []
    return [dict(row) for row in db.execute(text("""
        select p.payment_id as id, p.user_id, coalesce(u.name, u.whatsapp_name, 'Unnamed user') as user_name,
               sp.plan_name as plan, p.amount, p.currency, p.payment_gateway,
               p.transaction_reference, p.payment_status, p.payment_date, p.created_at
        from public.payments p
        left join public.users u on u.user_id = p.user_id
        left join public.user_subscriptions us on us.subscription_id = p.subscription_id
        left join public.subscription_plans sp on sp.plan_id = us.plan_id
        order by p.payment_date desc nulls last, p.payment_id desc
    """)).mappings().all()]

@app.get('/api/v1/admin/business', dependencies=[Depends(admin)])
def admin_business(db: Session = Depends(get_db)):
    if engine.dialect.name != 'postgresql': return []
    return [dict(row) for row in db.execute(text("""
        select b.business_id as id, b.business_name, bi.industry_name, b.location,
               b.business_stage, b.target_customer, b.available_capital, b.objective,
               b.user_id, b.created_at
        from public.business_profiles b
        left join public.business_industries bi on bi.industry_id = b.industry_id
        order by b.created_at desc nulls last, b.business_id desc
    """)).mappings().all()]

@app.get('/api/v1/admin/ai-usage', dependencies=[Depends(admin)])
def admin_ai_usage(db: Session = Depends(get_db)):
    if engine.dialect.name != 'postgresql': return []
    return [dict(row) for row in db.execute(text("""
        select conversation_type, status, count(*) as conversations,
               min(created_at) as first_request, max(updated_at) as last_request
        from public.ai_conversations group by conversation_type, status
        order by last_request desc nulls last
    """)).mappings().all()]
