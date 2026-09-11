import random

from backend.models.digital_twin import DigitalTwinDevice
from backend.services.digital_twin import tick_once


def test_tick_updates_sensor_and_robot_for_one_tenant(db):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="sensor-1", name="Field moisture", kind="sensor",
            device_type="soil_moisture", state={"value": 40},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="robot-1", name="Rover", kind="robot",
            device_type="rover", position={"x": 0, "y": 0, "z": 0},
        ),
        DigitalTwinDevice(
            tenant_id=2, device_id="sensor-2", name="Other tenant", kind="sensor",
            device_type="soil_moisture", state={"value": 40},
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(7))

    assert {item["device_id"] for item in snapshots} == {"sensor-1", "robot-1"}
    assert snapshots[0]["state"]["value"] != 40
    assert snapshots[1]["position"] != {"x": 0, "y": 0, "z": 0}
    other = db.query(DigitalTwinDevice).filter_by(device_id="sensor-2").one()
    assert other.state["value"] == 40


def test_manual_control_source_is_preserved(db):
    device = DigitalTwinDevice(
        tenant_id=1, device_id="actuator-1", name="Irrigation relay", kind="actuator",
        device_type="pump", control_mode="manual", state={"command": "on"},
    )
    db.add(device)
    db.commit()

    snapshot = tick_once(db, tenant_id=1, rng=random.Random(1))[0]

    assert snapshot["control_mode"] == "manual"
    assert snapshot["state"]["control_source"] == "manual"
    assert snapshot["state"]["output"] == "active"


def test_local_iot_runtime_tracks_registry_commands_and_telemetry():
    from backend.services.local_iot_runtime import LocalIotRuntime

    runtime = LocalIotRuntime()
    device = runtime.register_device(
        tenant_id=7,
        zone_id=3,
        device_id="pump-01",
        name="Booster Pump",
        kind="actuator",
        device_type="pump",
        metadata={"relay": "A1"},
    )

    assert device["device_id"] == "pump-01"
    assert runtime.list_zone_devices(3, tenant_id=7)[0]["device_id"] == "pump-01"

    queued = runtime.queue_command(
        device_id="pump-01",
        command="start",
        parameters={"flow": 24},
        zone_id=3,
        created_by="admin@demo",
    )
    assert queued["status"] == "queued"

    executed = runtime.execute_command(device_id="pump-01", command="start", parameters={"flow": 24}, actor="admin@demo")
    assert executed["state"]["last_command"] == "start"
    assert executed["state"]["last_actor"] == "admin@demo"

    telemetry = runtime.record_telemetry(
        device_id="pump-01",
        value=18.5,
        unit="L/min",
        sensor_type="flow",
        zone_id=3,
    )
    assert telemetry["telemetry"]["value"] == 18.5
    assert telemetry["state"]["last_value"] == 18.5

    snapshot = runtime.get_twin_snapshot()
    assert any(item["device_id"] == "pump-01" for item in snapshot["devices"])
    assert snapshot["command_queue"][0]["status"] == "executed"
    assert snapshot["events"][-1]["event_type"] == "telemetry_recorded"