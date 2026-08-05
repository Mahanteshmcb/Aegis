import pytest
from backend import crud, schemas

BASE = "/api/v1"


def setup_tenant_and_admin(test_db):
    SessionLocal = test_db
    db = SessionLocal()
    tenant = crud.create_tenant(db, schemas.TenantCreate(name="Test Tenant"))
    admin = crud.create_user(
        db,
        schemas.UserCreate(email="admin@aegis.com", password="admin1234", tenant_id=tenant.id, role="admin")
    )
    return db, tenant, admin


def test_admin_create_list_update_delete(client, test_db):
    db, tenant, admin = setup_tenant_and_admin(test_db)

    # Create a new operator user via admin endpoint
    payload = {"email": "operator1@example.com", "password": "opPass123", "role": "operator"}
    r = client.post(f"{BASE}/auth/users", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "email" in data and data["email"] == payload["email"]

    # List users as admin
    r2 = client.get(f"{BASE}/users")
    assert r2.status_code == 200
    users = r2.json()
    assert any(u["email"] == payload["email"] for u in users)

    # Find created user id
    created = next(u for u in users if u["email"] == payload["email"])
    user_id = created["id"]

    # Update role to admin
    r3 = client.put(f"{BASE}/users/{user_id}/role", json={"role": "admin"})
    assert r3.status_code == 200
    resp = r3.json()
    assert resp["role"] == "admin"

    # Prevent self-demotion: attempt to demote admin (id 1) to operator
    r4 = client.put(f"{BASE}/users/{admin.id}/role", json={"role": "viewer"})
    assert r4.status_code == 400

    # Delete the newly created user
    r5 = client.delete(f"{BASE}/users/{user_id}")
    assert r5.status_code == 200
    assert "deleted" in r5.json().get("message", "").lower()

    db.close()
