import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import Base
import backend.models_db
from backend import crud, schemas
from backend.main import app
from backend.dependencies import get_db
from fastapi.testclient import TestClient

os.environ.setdefault('PYTEST_RUNNING', '1')

path = tempfile.mktemp(suffix='.db', prefix='aegis_test_')
print('debug db', path)
engine = create_engine(f'sqlite:///{path}', connect_args={'check_same_thread': False}, echo=False)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

with SessionLocal() as db:
    tenant = crud.create_tenant(db, schemas.TenantCreate(name='Session Tenant'))
    admin = crud.create_user(db, schemas.UserCreate(email='admin@session.com', password='admin1234', tenant_id=tenant.id, role='admin'))
    print('created admin', admin.id, admin.email)

import backend.crud as backend_crud
orig_create_session = backend_crud.create_session

def wrapped_create_session(db, tenant_id, user_id, token_hash, token_type='access', expires_at=None):
    print('wrapped_create_session called', tenant_id, user_id, token_hash[:8], token_type, expires_at)
    result = orig_create_session(db, tenant_id, user_id, token_hash, token_type=token_type, expires_at=expires_at)
    print('wrapped_create_session committed', result.id)
    return result

backend_crud.create_session = wrapped_create_session

with TestClient(app) as client:
    response = client.post('/api/v1/auth/login', json={'email': 'admin@session.com', 'password': 'admin1234'})
    print('login status', response.status_code)
    print('login body', response.json())

with SessionLocal() as db:
    sessions = db.query(backend.models_db.Session).all()
    print('sessions count', len(sessions))
    for s in sessions:
        print('session', s.id, s.user_id, s.tenant_id, s.revoked, s.token_hash[:8])
