from datetime import datetime

from backend.dependencies import get_current_user
from backend.main import app
from backend.models.digital_twin import DigitalTwinDevice
from backend.models_db import AuditLog, DigitalTwinTelemetry, Sensor, SensorData


def test_legacy_sensor_ingestion_updates_canonical_twin_once_per_alert(test_db, client, monkeypatch):
    db = test_db()
    sensor = Sensor(
        tenant_id=1,
        name="hardware-canopy-temperature",
        type="SENSOR_TEMPERATURE",
    )
    db.add(sensor)
    db.commit()
    sensor_id = sensor.id
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="hardware-threshold-actuator",
        name="Hardware threshold actuator",
        kind="actuator",
        device_type="climate_relay",
        automation_policy={
            "source_device_id": f"legacy-sensor-{sensor_id}",
            "direction": "above",
            "threshold": 40,
            "on_command": "on",
            "off_command": "off",
        },
        state={"output": "idle"},
    ))
    db.commit()
    db.close()

    event_names = []

    async def capture_event(event, payload, tenant_id=None):
        event_names.append(event)

    monkeypatch.setattr("backend.routers.sensors.realtime.emit_tenant_event", capture_event)
    original_override = app.dependency_overrides[get_current_user]
    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "tenant_id": 1,
        "role": "operator",
        "email": "operator@example.com",
        "permissions": ["devices.manage", "devices.control"],
    }
    try:
        for value in (41.0, 41.0, 20.0):
            response = client.post(
                "/api/v1/sensors/data",
                json={
                    "sensor_id": sensor_id,
                    "value": value,
                    "unit": "C",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
            assert response.status_code == 200
    finally:
        app.dependency_overrides[get_current_user] = original_override

    verify_db = test_db()
    twin = verify_db.query(DigitalTwinDevice).filter_by(
        tenant_id=1,
        device_id=f"legacy-sensor-{sensor_id}",
    ).one()
    actuator = verify_db.query(DigitalTwinDevice).filter_by(
        device_id="hardware-threshold-actuator",
    ).one()
    assert twin.simulation_enabled is False
    assert twin.state["value"] == 20.0
    assert "alert" not in twin.state
    assert actuator.state["output"] == "idle"
    assert verify_db.query(SensorData).filter_by(sensor_id=sensor_id).count() == 3
    assert verify_db.query(DigitalTwinTelemetry).filter_by(device_id=twin.id).count() == 3
    assert verify_db.query(DigitalTwinTelemetry).filter_by(device_id=actuator.id).count() == 2
    audit_events = verify_db.query(AuditLog).filter(
        AuditLog.tenant_id == 1,
        AuditLog.entity_id == str(twin.id),
    ).all()
    assert {
        event.event_type for event in audit_events
        if (event.details or {}).get("device_id") == twin.device_id
    } == {"digital_twin.alert_started", "digital_twin.alert_recovered"}
    actuator_audits = verify_db.query(AuditLog).filter(
        AuditLog.tenant_id == 1,
        AuditLog.event_type == "digital_twin.automation_actuated",
    ).all()
    assert [
        event.details["output"]
        for event in actuator_audits
        if (event.details or {}).get("device_id") == actuator.device_id
    ] == ["active", "idle"]
    verify_db.close()

    assert event_names.count("digital_twin:device_update") == 5
    assert event_names.count("digital_twin:alert") == 1
    assert event_names.count("digital_twin:alert_cleared") == 1
