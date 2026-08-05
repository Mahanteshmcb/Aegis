from backend import crud, schemas
from backend.crud import create_session
BASE = "/api/v1"


def setup_tenant_and_admin(test_db):
    SessionLocal = test_db
    db = SessionLocal()
    tenant = crud.create_tenant(db, schemas.TenantCreate(name="Session Tenant"))
    admin = crud.create_user(
        db,
        schemas.UserCreate(email="admin@session.com", password="admin1234", tenant_id=tenant.id, role="admin")
    )
    return db, tenant, admin


def test_session_list_and_revoke(client, test_db):
    db, tenant, admin = setup_tenant_and_admin(test_db)

    # Perform login to create a session record
    login_payload = {"email": admin.email, "password": "admin1234"}
    r = client.post(f"{BASE}/auth/login", json=login_payload)
    assert r.status_code == 200
    data = r.json()
    access = data.get("access_token")
    assert access

    # List sessions (admin)
    r2 = client.get(f"{BASE}/sessions")
    assert r2.status_code == 200
    sessions = r2.json()
    assert isinstance(sessions, list)
    assert len(sessions) >= 1

    # Revoke first session
    sid = sessions[0]["id"]
    r3 = client.post(f"{BASE}/sessions/{sid}/revoke")
    assert r3.status_code == 200
    assert r3.json().get("message") == "Session revoked"

    db.close()
