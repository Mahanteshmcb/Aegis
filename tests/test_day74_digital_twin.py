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


def test_day76_sensor_reading_has_profile_and_threshold_metadata(db):
    db.add(DigitalTwinDevice(
        tenant_id=1, device_id="temperature-1", name="Canopy temperature", kind="sensor",
        device_type="temperature", state={"value": 34.5},
    ))
    db.commit()

    snapshot = tick_once(db, tenant_id=1, rng=random.Random(3))[0]
    state = snapshot["state"]

    assert 5.0 <= state["value"] <= 45.0
    assert state["unit"] == "C"
    assert state["reading_status"] in {"normal", "warning", "critical"}
    assert state["thresholds"]["warning"] == {"min": 10.0, "max": 35.0}
    assert state["thresholds"]["critical"] == {"min": 5.0, "max": 40.0}


def test_day76_sensor_reading_classifies_critical_value(db):
    db.add(DigitalTwinDevice(
        tenant_id=1, device_id="soil-1", name="Dry soil probe", kind="sensor",
        device_type="soil_moisture", state={"value": 5.0},
    ))
    db.commit()

    snapshot = tick_once(db, tenant_id=1, rng=random.Random(0))[0]

    assert snapshot["state"]["value"] < 10.0
    assert snapshot["state"]["reading_status"] == "critical"


def test_day77_low_soil_moisture_starts_irrigation(db):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="soil-automation", name="Dry soil", kind="sensor",
            device_type="soil_moisture", state={"value": 5.0},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="pump-automation", name="Irrigation pump", kind="actuator",
            device_type="pump", automation_policy={
                "source_device_id": "soil-automation", "direction": "below",
                "threshold": 20, "on_command": "on", "off_command": "off",
            },
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(0))
    pump = next(item for item in snapshots if item["device_id"] == "pump-automation")
    soil = next(item for item in snapshots if item["device_id"] == "soil-automation")

    assert pump["state"]["output"] == "active"
    assert pump["state"]["command"] == "on"
    assert pump["state"]["automation"]["matched"] is True
    assert soil["state"]["alert"]["severity"] == "critical"
    assert soil["alert"]["device_id"] == "soil-automation"
    assert soil["alert"]["tenant_id"] == 1


def test_day77_above_threshold_power_rule_turns_actuator_off(db):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="battery-automation", name="Battery", kind="sensor",
            device_type="battery", state={"value": 90.0},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="charger-automation", name="Battery charger", kind="actuator",
            device_type="charger", state={"command": "on"}, automation_policy={
                "source_device_id": "battery-automation", "direction": "above",
                "threshold": 80, "on_command": "off", "off_command": "on",
            },
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(0))
    charger = next(item for item in snapshots if item["device_id"] == "charger-automation")

    assert charger["state"]["output"] == "idle"
    assert charger["state"]["command"] == "off"
    assert charger["state"]["automation"]["matched"] is True


def test_day80_automation_lifecycle_runs_and_recovers(db):
    soil = DigitalTwinDevice(
        tenant_id=1, device_id="soil-lifecycle", name="Lifecycle soil", kind="sensor",
        device_type="soil_moisture", state={"value": 5.0},
    )
    pump = DigitalTwinDevice(
        tenant_id=1, device_id="pump-lifecycle", name="Lifecycle pump", kind="actuator",
        device_type="pump", automation_policy={
            "source_device_id": "soil-lifecycle", "direction": "below",
            "threshold": 20, "on_command": "on", "off_command": "off",
        },
    )
    manual_pump = DigitalTwinDevice(
        tenant_id=1, device_id="manual-pump-lifecycle", name="Manual pump", kind="actuator",
        device_type="pump", control_mode="manual", state={"command": "on"},
        automation_policy={
            "source_device_id": "soil-lifecycle", "direction": "below",
            "threshold": 20, "on_command": "off", "off_command": "on",
        },
    )
    db.add_all([soil, pump, manual_pump])
    db.commit()

    first_tick = tick_once(db, tenant_id=1, rng=random.Random(0))
    first_pump = next(item for item in first_tick if item["device_id"] == "pump-lifecycle")
    assert first_pump["state"]["output"] == "active"
    assert any(item.get("alert", {}).get("severity") == "critical" for item in first_tick)

    soil.state = {"value": 60.0}
    db.commit()
    second_tick = tick_once(db, tenant_id=1, rng=random.Random(0))
    second_pump = next(item for item in second_tick if item["device_id"] == "pump-lifecycle")
    second_manual = next(item for item in second_tick if item["device_id"] == "manual-pump-lifecycle")

    assert second_pump["state"]["output"] == "idle"
    assert second_pump["state"]["automation"]["matched"] is False
    assert not any(item.get("alert") for item in second_tick)
    assert second_manual["state"]["command"] == "on"
    assert second_manual["state"]["control_source"] == "manual"


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