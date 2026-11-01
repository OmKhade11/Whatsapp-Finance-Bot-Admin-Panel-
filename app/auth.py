from datetime import datetime
from fastapi import Depends, Header, HTTPException
import requests
from sqlalchemy import text
from sqlalchemy.orm import Session
from .config import settings
from .db import engine, get_db
from .models import Subscription

def current_user(x_user_id: str | None = Header(default=None)):
    if not x_user_id: raise HTTPException(401, 'authentication required')
    return x_user_id

def entitlement(tier: str):
    def check(user_id=Depends(current_user), db: Session = Depends(get_db)):
        sub = db.query(Subscription).filter_by(user_id=user_id).first()
        actual = sub.tier if sub and sub.active and (not sub.expires_at or sub.expires_at > datetime.utcnow()) else 'FREE'
        ranks = {'FREE': 0, 'PLUS': 1, 'PREMIUM': 2}
        if ranks.get(actual, 0) < ranks[tier]: raise HTTPException(403, {'code': 'UPGRADE_REQUIRED', 'required_tier': tier, 'current_tier': actual})
        return user_id
    return check

def admin(authorization: str | None = Header(default=None), x_admin: str | None = Header(default=None), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith('bearer '):
        token = authorization.split(' ', 1)[1].strip()
        try:
            response = requests.get(
                settings.supabase_url.rstrip('/') + '/auth/v1/user',
                headers={'apikey': settings.supabase_anon_key, 'Authorization': f'Bearer {token}'},
                timeout=10,
            )
        except requests.RequestException as exc:
            raise HTTPException(503, 'authentication service unavailable') from exc
        if response.status_code != 200:
            raise HTTPException(401, 'invalid or expired admin session')
        auth_user_id = response.json().get('id')
        if not auth_user_id:
            raise HTTPException(401, 'invalid admin identity')
        if engine.dialect.name != 'postgresql':
            raise HTTPException(503, 'admin role database is unavailable')
        allowed = db.execute(text("""
            select exists (
                select 1 from public.admin_users au
                join public.admin_roles ar on ar.role_id = au.admin_role_id
                where au.auth_user_id = :auth_user_id
                  and upper(coalesce(au.status, '')) = 'ACTIVE'
                  and upper(coalesce(ar.status, '')) = 'ACTIVE'
            )
        """), {'auth_user_id': auth_user_id}).scalar()
        if not allowed:
            raise HTTPException(403, 'admin role required')
        return auth_user_id
    if settings.allow_dev_admin_header and x_admin == 'true':
        return 'development-admin'
    raise HTTPException(401, 'Supabase admin session required')
