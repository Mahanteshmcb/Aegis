from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from backend.models.digital_twin import DigitalTwinDevice
from backend.routers import digital_twin


class User:
    def __init__(self, tenant_id):
        self.tenant_id = tenant_id


def test_day81_device_crud_is_tenant_scoped(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    owner = User(tenant_id=1)
    other_tenant = User(tenant_id=2)

    created = digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="crud-sensor-1",
            name="CRUD moisture probe",
            kind="sensor",
            device_type="soil_moisture",
            state={"value": 42},
        ),
        owner,
    )

    assert created["device_id"] == "crud-sensor-1"
    assert created["tenant_id"] == 1

    updated = digital_twin.update_device(
        created["id"],
        digital_twin.DeviceUpdate(name="Updated moisture probe", status="maintenance"),
        owner,
    )
    assert updated["name"] == "Updated moisture probe"
    assert updated["status"] == "maintenance"

    with pytest.raises(HTTPException) as error:
        digital_twin.delete_device(created["id"], other_tenant)
    assert error.value.status_code == 404

    deleted = digital_twin.delete_device(created["id"], owner)
    assert deleted == {"deleted": True, "device_id": "crud-sensor-1"}
    assert db.query(DigitalTwinDevice).filter_by(device_id="crud-sensor-1").first() is None


def test_day83_twin_health_reports_online_devices_and_alerts(db, monkeypatch):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="health-sensor", name="Health sensor", kind="sensor",
            device_type="temperature", status="online", state={"reading_status": "warning"},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="health-pump", name="Health pump", kind="actuator",
            device_type="pump", status="online", state={"output": "active"},
        ),
        DigitalTwinDevice(
            tenant_id=2, device_id="other-device", name="Other tenant", kind="sensor",
            device_type="temperature", status="offline",
        ),
    ])
    db.commit()
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))

    health = digital_twin.twin_health(User(tenant_id=1))

    assert health["devices"] == 2
    assert health["online"] == 2
    assert health["sensors"] == 1
    assert health["actuators"] == 1
    assert health["active_actuators"] == 1
    assert health["alerts"] == 1
    assert health["health_score"] == 100
