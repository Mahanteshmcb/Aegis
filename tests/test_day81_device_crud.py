from contextlib import nullcontext

import pytest
from fastapi import HTTPException

from backend.models.digital_twin import DigitalTwinDevice
from backend.routers import digital_twin


class User:
    def __init__(self, tenant_id, role="operator"):
        self.tenant_id = tenant_id
        self.role = role


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
            position={"x": 4.5, "y": 1.2, "z": -3.0},
            orientation={"x": 0.0, "y": 90.0, "z": 0.0},
            spatial_status="surveyed",
            coordinate_system="estate-local-y-up",
        ),
        owner,
    )

    assert created["device_id"] == "crud-sensor-1"
    assert created["tenant_id"] == 1
    assert created["position"] == {"x": 4.5, "y": 1.2, "z": -3.0}
    assert created["position_configured"] is True
    assert created["orientation"] == {"x": 0.0, "y": 90.0, "z": 0.0}
    assert created["spatial_status"] == "surveyed"

    updated = digital_twin.update_device(
        created["id"],
        digital_twin.DeviceUpdate(
            expected_last_updated=created["last_updated"],
            name="Updated moisture probe",
            status="maintenance",
            position={"x": 8, "y": 1, "z": -2},
            orientation={"x": 0, "y": 180, "z": 0},
        ),
        owner,
    )
    assert updated["name"] == "Updated moisture probe"
    assert updated["status"] == "maintenance"
    assert updated["position"] == {"x": 8, "y": 1, "z": -2}
    assert updated["position_configured"] is True
    assert updated["orientation"] == {"x": 0, "y": 180, "z": 0}

    with pytest.raises(HTTPException) as stale_error:
        digital_twin.update_device(
            created["id"],
            digital_twin.DeviceUpdate(
                expected_last_updated=created["last_updated"],
                name="Stale write",
            ),
            owner,
        )
    assert stale_error.value.status_code == 409

    with pytest.raises(HTTPException) as error:
        digital_twin.delete_device(created["id"], other_tenant)
    assert error.value.status_code == 404

    deleted = digital_twin.delete_device(created["id"], owner)
    assert deleted == {"deleted": True, "device_id": "crud-sensor-1"}
    assert db.query(DigitalTwinDevice).filter_by(device_id="crud-sensor-1").first() is None


def test_device_spatial_vectors_reject_non_finite_and_incomplete_values():
    with pytest.raises(ValueError):
        digital_twin.DeviceUpdate(position={"x": 1, "y": float("nan"), "z": 0})

    with pytest.raises(ValueError):
        digital_twin.DeviceUpdate(orientation={"x": 0, "y": 0})


def test_origin_is_preserved_as_an_explicit_device_position(db, monkeypatch):
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))
    created = digital_twin.create_device(
        digital_twin.DeviceCreate(
            device_id="origin-device",
            name="Origin device",
            kind="sensor",
            device_type="temperature",
        ),
        User(tenant_id=1),
    )
    assert created["position_configured"] is False

    updated = digital_twin.update_device(
        created["id"],
        digital_twin.DeviceUpdate(position={"x": 0, "y": 0, "z": 0}),
        User(tenant_id=1),
    )
    assert updated["position"] == {"x": 0, "y": 0, "z": 0}
    assert updated["position_configured"] is True


def test_surveyed_device_requires_coordinate_system():
    with pytest.raises(HTTPException) as error:
        digital_twin.create_device(
            digital_twin.DeviceCreate(
                device_id="surveyed-no-frame",
                name="Surveyed device",
                kind="sensor",
                device_type="temperature",
                spatial_status="surveyed",
            ),
            User(tenant_id=1),
        )
    assert error.value.status_code == 422


def test_surveyed_device_requires_explicit_position():
    with pytest.raises(HTTPException) as error:
        digital_twin.create_device(
            digital_twin.DeviceCreate(
                device_id="surveyed-no-position",
                name="Surveyed device",
                kind="sensor",
                device_type="temperature",
                spatial_status="surveyed",
                coordinate_system="estate-local-y-up",
            ),
            User(tenant_id=1),
        )
    assert error.value.status_code == 422


def test_inferred_device_cannot_be_marked_surveyed_without_new_position(db, monkeypatch):
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="inferred-to-surveyed",
        name="Inferred device",
        kind="sensor",
        device_type="temperature",
    )
    db.add(device)
    db.commit()
    monkeypatch.setattr(digital_twin, "SessionLocal", lambda: nullcontext(db))

    with pytest.raises(HTTPException) as error:
        digital_twin.update_device(
            device.id,
            digital_twin.DeviceUpdate(
                spatial_status="surveyed",
                coordinate_system="estate-local-y-up",
            ),
            User(tenant_id=1),
        )

    assert error.value.status_code == 422


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
