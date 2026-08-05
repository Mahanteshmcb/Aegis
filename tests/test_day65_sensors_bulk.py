from backend import crud, schemas
BASE = "/api/v1"


def setup_tenant_and_admin(test_db):
    SessionLocal = test_db
    db = SessionLocal()
    tenant = crud.create_tenant(db, schemas.TenantCreate(name="Sensors Tenant"))
    admin = crud.create_user(
        db,
        schemas.UserCreate(email="admin@sensors.com", password="admin1234", tenant_id=tenant.id, role="admin")
    )
    return db, tenant, admin


def test_sensors_bulk_import(client, test_db):
    db, tenant, admin = setup_tenant_and_admin(test_db)

    csv_content = "name,type,location,zone_id\nSensor A,temperature,Lab,\nSensor B,humidity,Greenhouse,1\n"
    files = {"file": ("sensors.csv", csv_content, "text/csv")}
    r = client.post(f"{BASE}/sensors/bulk_import", files=files)
    assert r.status_code == 200
    summary = r.json().get("summary")
    assert summary["created"] == 2

    # Re-run with updated location for Sensor A to trigger update
    csv_content2 = "name,type,location,zone_id\nSensor A,temperature,Lab Updated,\n"
    files = {"file": ("sensors.csv", csv_content2, "text/csv")}
    r2 = client.post(f"{BASE}/sensors/bulk_import", files=files)
    assert r2.status_code == 200
    summary2 = r2.json().get("summary")
    assert summary2["updated"] == 1

    db.close()
