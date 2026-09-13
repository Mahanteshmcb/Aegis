import asyncio
from datetime import datetime

from backend.models_db import Tenant, Sensor
from backend.models.safety import SafetyRule, SafetyEvent, EmergencyStop
from backend.models.lab_automation import AutomationJob
from backend.services.automation_scheduler import check_safety_for_tenant, _execute_job


def create_tenant(session):
    tenant = Tenant(name=f"Tenant {datetime.utcnow().timestamp()}")
    session.add(tenant)
    session.commit()
    session.refresh(tenant)
    return tenant


def test_storage_facilities_and_inventory_endpoints(client, test_db):
    db = test_db()
    create_tenant(db)
    headers = {"Authorization": "Bearer test-token"}

    facility_payload = {
        "name": "Seed Vault A",
        "location": "Basement 1",
        "type": "cold",
        "capacity": 150.0,
    }
    resp = client.post("/api/v1/storage/facilities", json=facility_payload, headers=headers)
    assert resp.status_code == 200
    facility = resp.json()
    assert facility["name"] == facility_payload["name"]
    assert facility["location"] == facility_payload["location"]
    assert facility["type"] == facility_payload["type"]

    inventory_payload = {
        "facility_id": facility["id"],
        "name": "Cryogenic Seed Batch",
        "description": "High-value seed inventory",
        "quantity": 12.5,
        "unit": "kg",
        "lot_number": "SEED-2026-01",
        "expires_at": datetime.utcnow().isoformat(),
    }
    resp = client.post("/api/v1/storage/inventory", json=inventory_payload, headers=headers)
    assert resp.status_code == 200
    item = resp.json()
    assert item["facility_id"] == facility["id"]
    assert item["name"] == inventory_payload["name"]

    list_resp = client.get("/api/v1/storage/facilities", headers=headers)
    assert list_resp.status_code == 200
    facilities = list_resp.json()
    assert any(f["id"] == facility["id"] for f in facilities)

    items_resp = client.get("/api/v1/storage/inventory", headers=headers)
    assert items_resp.status_code == 200
    items = items_resp.json()
    assert any(i["id"] == item["id"] for i in items)


def test_check_safety_blocks_for_active_estop(test_db):
    db = test_db()
    tenant = create_tenant(db)
    estop = EmergencyStop(tenant_id=tenant.id, active=True, reason="Test emergency stop")
    db.add(estop)
    db.commit()

    blocked, reason, rule_id = check_safety_for_tenant(db, tenant.id)
    assert blocked is True
    assert "Emergency Stop active" in reason
    assert rule_id is None


def test_execute_job_blocks_when_safety_rule_violates(test_db, monkeypatch):
    db = test_db()
    tenant = create_tenant(db)

    sensor = Sensor(
        tenant_id=tenant.id,
        type="air_quality",
        location="Lab 1",
        last_reading={"co2": {"ppm": 1200}},
    )
    db.add(sensor)

    rule = SafetyRule(
        tenant_id=tenant.id,
        name="CO2 limit",
        sensor_type="air",
        metric="co2.ppm",
        operator="gt",
        threshold=1000.0,
        severity="critical",
        enabled=True,
    )
    db.add(rule)
    db.commit()

    job = AutomationJob(
        tenant_id=tenant.id,
        device_id=None,
        name="Test HVAC Activation",
        command="activate_climate_control",
        scheduled_at=datetime.utcnow(),
        status="pending",
    )
    db.add(job)
    db.commit()

    async def no_sleep(duration):
        return None

    monkeypatch.setattr("backend.services.automation_scheduler.asyncio.sleep", no_sleep)

    async def run_job():
        await _execute_job(db, job)

    asyncio.get_event_loop().run_until_complete(run_job())
    db.refresh(job)

    assert job.status == "blocked"
    event = db.query(SafetyEvent).filter(SafetyEvent.tenant_id == tenant.id).first()
    assert event is not None
    assert "blocked at execution" in event.message
    assert event.severity == "critical"
