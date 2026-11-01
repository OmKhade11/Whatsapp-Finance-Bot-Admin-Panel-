from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine, SessionLocal
from app.models import Subscription

Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
client = TestClient(app)

def setup_function():
    db = SessionLocal(); db.query(Subscription).delete(); db.commit()
    for table in reversed(Base.metadata.sorted_tables):
        if table.name != 'subscriptions': db.execute(table.delete())
    db.commit(); db.close()

def plus(user='a'):
    db = SessionLocal(); db.add(Subscription(user_id=user, tier='PLUS', active=True)); db.commit(); db.close()

def test_auth_and_entitlement():
    assert client.post('/api/v1/income', headers={'X-User-ID':'a'}, json={'amount': 10, 'entry_date':'2026-10-01'}).status_code == 403
    plus()
    assert client.post('/api/v1/income', headers={'X-User-ID':'a'}, json={'amount': 50000, 'entry_date':'2026-10-01'}).status_code == 200

def test_isolation_and_budget():
    plus('a')
    response = client.post('/api/v1/income', headers={'X-User-ID':'a'}, json={'amount':50000,'entry_date':'2026-10-01'})
    item_id = response.json()['id']
    assert client.put(f'/api/v1/income/{item_id}', headers={'X-User-ID':'b'}, json={'amount':1,'entry_date':'2026-10-01'}).status_code == 403
    plus('b')
    assert client.put(f'/api/v1/income/{item_id}', headers={'X-User-ID':'b'}, json={'amount':1,'entry_date':'2026-10-01'}).status_code == 404
    client.post('/api/v1/expenses', headers={'X-User-ID':'a'}, json={'category':'rent','amount':40000,'entry_date':'2026-10-02'})
    result = client.get('/api/v1/budgets?month=2026-10', headers={'X-User-ID':'a'}).json()
    assert result['balance'] == 10000 and result['status'] == 'SURPLUS'

def test_payment_callback_idempotency_and_premium():
    payload = {'event_id':'evt1','user_id':'a','tier':'PREMIUM'}
    assert client.post('/api/v1/webhooks/payment', json=payload).json()['duplicate'] is False
    assert client.post('/api/v1/webhooks/payment', json=payload).json()['duplicate'] is True
    assert client.post('/api/v1/capital/calculate', headers={'X-User-ID':'a'}, json={'costs':{'Equipment':100}}).status_code == 200

def test_health_openapi_and_invalid_input():
    assert client.get('/health').json()['status'] == 'healthy'
    assert client.get('/openapi.json').status_code == 200
    assert client.post('/api/v1/budgets/calculate', headers={'X-User-ID':'a'}, json={'monthly_income':1,'needs_percent':20,'investment_percent':20,'savings_percent':20}).status_code == 422
