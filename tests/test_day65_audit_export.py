from backend import crud, schemas
from backend.crud import create_audit_log_with_transaction
BASE = "/api/v1"


def setup_tenant_and_admin(test_db):
    SessionLocal = test_db
    db = SessionLocal()
    tenant = crud.create_tenant(db, schemas.TenantCreate(name="Audit Tenant"))
    admin = crud.create_user(
        db,
        schemas.UserCreate(email="admin@audit.com", password="admin1234", tenant_id=tenant.id, role="admin")
    )
    return db, tenant, admin


def test_audit_export(client, test_db):
    db, tenant, admin = setup_tenant_and_admin(test_db)
    headers = {"Authorization": "Bearer test-token"}

    # create a few audit logs
    for i in range(3):
        create_audit_log_with_transaction(db, event_type="user_created", data_hash=f"h{i}", tenant_id=tenant.id)

    r = client.get(f"{BASE}/audit/export", headers=headers)
    assert r.status_code == 200
    text = r.text
    assert "event_type" in text or "user_created" in text

    db.close()
