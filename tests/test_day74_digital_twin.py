import random

import pytest

from backend.database import Zone
from backend.models.digital_twin import DigitalTwinDevice
from backend.models.safety import EmergencyStop
from backend.models_db import AuditLog, DigitalTwinTelemetry
from backend.audit_utils import record_actor_audit_event
from backend.services import digital_twin
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
    assert snapshots[1]["position"] == {"x": 0, "y": 0, "z": 0}
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


def test_actor_audit_envelope_cannot_be_overridden_by_details(db):
    event = record_actor_audit_event(
        db,
        1,
        {"id": 17, "email": "operator@example.com"},
        "device_controlled",
        "digital_twin_device",
        42,
        {
            "action": "forged_action",
            "actor_user_id": 99,
            "actor_email": "forged@example.com",
            "entity_type": "forged_entity",
            "entity_id": "999",
            "outcome": "failure",
        },
    )

    assert event.action == "device_controlled"
    assert event.actor_user_id == 17
    assert event.actor_email == "operator@example.com"
    assert event.entity_type == "digital_twin_device"
    assert event.entity_id == "42"
    assert event.outcome == "success"


def test_robot_stop_command_halts_simulated_motion(db):
    robot = DigitalTwinDevice(
        tenant_id=1,
        device_id="stop-test-robot",
        name="Stop test robot",
        kind="robot",
        device_type="rover",
        position={"x": 12, "y": 0, "z": -8},
        state={"command": "stop", "activity": "patrolling"},
    )
    db.add(robot)
    db.commit()

    snapshot = tick_once(db, tenant_id=1, rng=random.Random(7))[0]

    assert snapshot["position"] == {"x": 12, "y": 0, "z": -8}
    assert snapshot["state"]["activity"] == "stopped"


def test_actuator_off_command_turns_output_idle(db):
    actuator = DigitalTwinDevice(
        tenant_id=1,
        device_id="off-test-actuator",
        name="Off test actuator",
        kind="actuator",
        device_type="pump",
        state={"command": "off", "output": "active"},
    )
    db.add(actuator)
    db.commit()

    snapshot = tick_once(db, tenant_id=1, rng=random.Random(7))[0]

    assert snapshot["state"]["output"] == "idle"


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


def test_sensor_alert_emits_once_per_episode_and_clears_on_recovery(db, monkeypatch):
    sensor = DigitalTwinDevice(
        tenant_id=1, device_id="alert-lifecycle", name="Canopy temperature",
        kind="sensor", device_type="temperature", state={"value": 20.0},
    )
    db.add(sensor)
    db.commit()

    values = iter((39.0, 41.0, 41.0, 20.0, 41.0))
    monkeypatch.setattr(
        digital_twin,
        "_environment_step",
        lambda device, devices, step_seconds: (next(values), {"model": "test"}),
    )
    first = tick_once(db, tenant_id=1)[0]
    first_event_id = first["alert"]["event_id"]
    escalation = tick_once(db, tenant_id=1)[0]
    continued = tick_once(db, tenant_id=1)[0]

    assert first["alert"]["severity"] == "warning"
    assert escalation["alert"]["severity"] == "critical"
    assert escalation["alert"]["event_id"] == first_event_id
    assert "alert" not in continued
    assert continued["state"]["alert"]["event_id"] == first_event_id

    recovered = tick_once(db, tenant_id=1)[0]
    assert recovered["alert_cleared"]["event_id"] == first_event_id
    assert "alert" not in recovered["state"]

    recurrence = tick_once(db, tenant_id=1)[0]
    assert recurrence["alert"]["event_id"] != first_event_id
    transitions = [
        event
        for event in db.query(AuditLog).filter(
            AuditLog.tenant_id == 1,
            AuditLog.entity_id == str(sensor.id),
        ).order_by(AuditLog.id).all()
        if (event.details or {}).get("device_id") == "alert-lifecycle"
    ]
    assert [event.event_type for event in transitions] == [
        "digital_twin.alert_started",
        "digital_twin.alert_escalated",
        "digital_twin.alert_recovered",
        "digital_twin.alert_started",
    ]
    assert transitions[0].actor_email == "system@aegis.local"
    assert transitions[0].details["severity"] == "warning"


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
    automation_events = [
        event
        for event in db.query(AuditLog).filter(
            AuditLog.event_type == "digital_twin.automation_actuated",
            AuditLog.entity_id == str(pump["id"]),
        ).all()
        if (event.details or {}).get("device_id") == "pump-automation"
    ]
    assert len(automation_events) == 1
    assert automation_events[0].details["source_device_id"] == "soil-automation"

    tick_once(db, tenant_id=1, rng=random.Random(0))
    assert len([
        event
        for event in db.query(AuditLog).filter(
            AuditLog.event_type == "digital_twin.automation_actuated",
            AuditLog.entity_id == str(pump["id"]),
        ).all()
        if (event.details or {}).get("device_id") == "pump-automation"
    ]) == 1


def test_automation_does_not_act_on_an_offline_source_or_actuator(db):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="offline-source", name="Offline soil probe",
            kind="sensor", device_type="soil_moisture", status="offline",
            state={"value": 5.0, "reading_status": "critical"},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="offline-source-pump", name="Source-protected pump",
            kind="actuator", device_type="pump",
            automation_policy={
                "source_device_id": "offline-source",
                "direction": "below",
                "threshold": 20,
                "on_command": "on",
                "off_command": "off",
            },
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="offline-pump", name="Offline pump",
            kind="actuator", device_type="pump", status="offline",
            state={"command": "off", "output": "idle"},
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(0))
    source = next(item for item in snapshots if item["device_id"] == "offline-source")
    source_pump = next(item for item in snapshots if item["device_id"] == "offline-source-pump")
    offline_pump = next(item for item in snapshots if item["device_id"] == "offline-pump")

    assert source["state"]["value"] == 5.0
    assert source_pump["state"]["output"] == "idle"
    assert source_pump["state"]["automation"]["blocked_reason"] == "source_device_unavailable"
    assert offline_pump["status"] == "offline"
    assert offline_pump["state"]["output"] == "idle"


def test_automation_source_resolution_is_tenant_scoped(db):
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1, device_id="shared-probe", name="Tenant one probe",
            kind="sensor", device_type="soil_moisture", control_mode="manual",
            state={"value": 10.0},
        ),
        DigitalTwinDevice(
            tenant_id=2, device_id="shared-probe", name="Tenant two probe",
            kind="sensor", device_type="soil_moisture", control_mode="manual",
            state={"value": 90.0},
        ),
        DigitalTwinDevice(
            tenant_id=1, device_id="pump-one", name="Tenant one pump",
            kind="actuator", device_type="pump",
            automation_policy={
                "source_device_id": "shared-probe",
                "direction": "above",
                "threshold": 50,
                "on_command": "on",
                "off_command": "off",
            },
        ),
        DigitalTwinDevice(
            tenant_id=2, device_id="pump-two", name="Tenant two pump",
            kind="actuator", device_type="pump",
            automation_policy={
                "source_device_id": "shared-probe",
                "direction": "above",
                "threshold": 50,
                "on_command": "on",
                "off_command": "off",
            },
        ),
    ])
    db.commit()

    snapshots = tick_once(db, rng=random.Random(0))
    pumps = {item["device_id"]: item for item in snapshots if item["kind"] == "actuator"}

    assert pumps["pump-one"]["state"]["output"] == "idle"
    assert pumps["pump-two"]["state"]["output"] == "active"


def test_soil_moisture_responds_to_active_zone_irrigation(db):
    zone = Zone(tenant_id=1, name="Irrigation test zone")
    db.add(zone)
    db.commit()
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1,
            zone_id=zone.id,
            device_id="soil-water-balance",
            name="Soil water balance probe",
            kind="sensor",
            device_type="soil_moisture",
            state={
                "value": 30.0,
                "simulation_model": {
                    "drainage_rate_per_minute": 0,
                    "infiltration_rate_per_minute": 60,
                },
            },
        ),
        DigitalTwinDevice(
            tenant_id=1,
            zone_id=zone.id,
            device_id="zone-irrigation-pump",
            name="Zone irrigation pump",
            kind="actuator",
            device_type="pump",
            state={"command": "on", "output": "active", "flow": 2},
        ),
        DigitalTwinDevice(
            tenant_id=2,
            zone_id=zone.id,
            device_id="other-tenant-pump",
            name="Other tenant pump",
            kind="actuator",
            device_type="pump",
            state={"command": "on", "output": "active", "flow": 50},
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(0))
    soil = next(item for item in snapshots if item["device_id"] == "soil-water-balance")

    assert soil["state"]["value"] == 32.0
    assert soil["state"]["simulation"]["model"] == "soil_moisture_water_balance"
    assert soil["state"]["simulation"]["contributing_actuators"] == ["zone-irrigation-pump"]


def test_thermal_demo_model_relaxes_toward_ambient_deterministically(db):
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="thermal-demo-probe",
        name="Thermal demo probe",
        kind="sensor",
        device_type="temperature",
        state={
            "value": 30.0,
            "simulation_model": {
                "kind": "thermal_rc",
                "ambient_temperature_c": 20.0,
                "time_constant_seconds": 60.0,
            },
        },
    ))
    db.commit()

    snapshot = tick_once(db, tenant_id=1, step_seconds=60.0)[0]

    assert snapshot["state"]["value"] == 23.68
    assert snapshot["state"]["simulation"]["model"] == "first_order_environment_demo"
    assert snapshot["state"]["simulation"]["assumption"] == "generic_uncalibrated_demo_parameters"


def test_structural_demo_model_integrates_damped_displacement(db):
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="structure-demo-sensor",
        name="Structure demo displacement",
        kind="sensor",
        device_type="structural_displacement",
        state={
            "value": 0.0,
            "simulation_model": {
                "kind": "single_degree_of_freedom",
                "mass_kg": 1.0,
                "natural_frequency_hz": 1.0 / (2.0 * 3.141592653589793),
                "damping_ratio": 0.0,
                "force_newtons": 1.0,
            },
        },
    ))
    db.commit()

    snapshot = tick_once(db, tenant_id=1, step_seconds=0.1)[0]

    assert snapshot["state"]["value"] == 10.0
    assert snapshot["state"]["unit"] == "mm"
    assert snapshot["state"]["simulation"]["model"] == "single_degree_of_freedom_structure_demo"
    assert snapshot["state"]["simulation_state"]["displacement_m"] == pytest.approx(0.01)


def test_water_tank_demo_model_balances_tenant_scoped_actuator_flows(db):
    zone = Zone(tenant_id=1, name="Tank simulation zone")
    db.add(zone)
    db.commit()
    db.add_all([
        DigitalTwinDevice(
            tenant_id=1,
            zone_id=zone.id,
            device_id="tank-level-demo",
            name="Tank level",
            kind="sensor",
            device_type="water_level",
            state={
                "value": 50.0,
                "simulation_model": {
                    "kind": "water_tank",
                    "capacity_liters": 1000.0,
                },
            },
        ),
        DigitalTwinDevice(
            tenant_id=1,
            zone_id=zone.id,
            device_id="tank-fill-demo",
            name="Tank fill pump",
            kind="actuator",
            device_type="pump",
            state={
                "output": "active",
                "simulation_model": {"flow_direction": "inflow", "flow_lpm": 60.0},
            },
        ),
        DigitalTwinDevice(
            tenant_id=1,
            zone_id=zone.id,
            device_id="tank-drain-demo",
            name="Tank drain valve",
            kind="actuator",
            device_type="valve",
            state={
                "output": "active",
                "simulation_model": {"flow_direction": "outflow", "flow_lpm": 20.0},
            },
        ),
        DigitalTwinDevice(
            tenant_id=2,
            zone_id=zone.id,
            device_id="other-tenant-fill",
            name="Other tenant pump",
            kind="actuator",
            device_type="pump",
            state={
                "output": "active",
                "simulation_model": {"flow_direction": "inflow", "flow_lpm": 500.0},
            },
        ),
    ])
    db.commit()

    snapshots = tick_once(db, tenant_id=1, step_seconds=60.0)
    tank = next(item for item in snapshots if item["device_id"] == "tank-level-demo")

    assert tank["state"]["value"] == 54.0
    assert tank["state"]["simulation"]["inflow_lpm"] == 60.0
    assert tank["state"]["simulation"]["outflow_lpm"] == 20.0
    assert tank["state"]["simulation"]["contributing_actuators"] == [
        "tank-fill-demo",
        "tank-drain-demo",
    ]


def test_robot_demo_kinematics_obey_speed_target_and_stop(db):
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="kinematic-demo-rover",
        name="Kinematic demo rover",
        kind="robot",
        device_type="rover",
        position={"x": 0.0, "y": 0.0, "z": 0.0},
        state={
            "activity": "moving",
            "battery": 80.0,
            "navigation_target": {"x": 10.0, "y": 0.0, "z": 0.0},
            "simulation_model": {
                "kind": "robot_kinematics",
                "max_speed_units_per_second": 1.0,
                "battery_capacity_wh": 600.0,
                "moving_load_w": 90.0,
                "idle_load_w": 12.0,
            },
        },
    ))
    db.commit()

    moving = tick_once(db, tenant_id=1, step_seconds=2.0)[0]

    assert moving["position"] == {"x": 2.0, "y": 0.0, "z": 0.0}
    assert moving["state"]["activity"] == "moving"
    assert moving["state"]["battery"] == pytest.approx(79.991667)
    assert moving["state"]["simulation"]["model"] == "robot_point_kinematics_demo"

    robot = db.query(DigitalTwinDevice).filter_by(device_id="kinematic-demo-rover").one()
    robot.state = {**robot.state, "command": "stop"}
    db.commit()
    stopped = tick_once(db, tenant_id=1, step_seconds=2.0)[0]

    assert stopped["position"] == {"x": 2.0, "y": 0.0, "z": 0.0}
    assert stopped["state"]["activity"] == "stopped"
    assert stopped["state"]["navigation_target"] == {"x": 10.0, "y": 0.0, "z": 0.0}


@pytest.mark.parametrize(
    "state, message",
    [
        ({"simulation_model": {"kind": "unsupported"}}, "Unsupported robot simulation model"),
        (
            {
                "battery": 80.0,
                "simulation_model": {
                    "kind": "robot_kinematics",
                    "battery_capacity_wh": 0,
                },
            },
            "Invalid robot energy simulation parameters",
        ),
    ],
)
def test_robot_simulation_rejects_unsupported_or_invalid_models(db, state, message):
    db.add(DigitalTwinDevice(
        tenant_id=1,
        device_id="invalid-model-rover",
        name="Invalid model rover",
        kind="robot",
        device_type="rover",
        state=state,
    ))
    db.commit()

    with pytest.raises(ValueError, match=message):
        tick_once(db, tenant_id=1)


def test_simulation_rejects_nonpositive_or_nonfinite_step(db):
    for invalid_step in (0, -1, float("inf"), float("nan")):
        try:
            tick_once(db, tenant_id=1, step_seconds=invalid_step)
        except ValueError as exc:
            assert "finite positive" in str(exc)
        else:
            raise AssertionError(f"Expected invalid simulation step to fail: {invalid_step}")


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


def test_device_lifecycle_and_command_write_structured_audit(client, test_db, monkeypatch):
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": "audited-pump",
        "name": "Audited Pump",
        "kind": "actuator",
        "device_type": "pump",
        "state": {"output": "idle"},
    })
    assert created.status_code == 200, created.text
    device_id = created.json()["id"]

    updated = client.put(f"/api/v1/digital-twin/devices/{device_id}", headers=headers, json={"name": "Updated Pump"})
    assert updated.status_code == 200, updated.text
    commanded = client.post(f"/api/v1/digital-twin/devices/{device_id}/control", headers=headers, json={"command": "on"})
    assert commanded.status_code == 200, commanded.text
    deleted = client.delete(f"/api/v1/digital-twin/devices/{device_id}", headers=headers)
    assert deleted.status_code == 200, deleted.text

    audit_db = test_db()
    try:
        logs = audit_db.query(AuditLog).filter(AuditLog.entity_id == "audited-pump").order_by(AuditLog.id).all()
        assert [log.event_type for log in logs] == ["device_created", "device_updated", "device_commanded", "device_deleted"]
        command_log = logs[2]
        assert command_log.actor_email == "admin@aegis.com"
        assert command_log.entity_type == "actuator"
        assert command_log.action == "device_commanded"
        assert command_log.details["command"] == "on"
        assert command_log.details["response"]["state"]["command"] == "on"
    finally:
        audit_db.close()


def test_active_emergency_stop_blocks_digital_twin_commands(client, test_db, monkeypatch):
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": "estop-protected-actuator",
        "name": "Protected actuator",
        "kind": "actuator",
        "device_type": "relay",
        "state": {"output": "idle"},
    })
    assert created.status_code == 200, created.text

    db = test_db()
    try:
        db.add(EmergencyStop(tenant_id=1, active=True, reason="Test emergency stop"))
        db.commit()
    finally:
        db.close()

    safety = client.get("/api/v1/digital-twin/safety-status", headers=headers)
    assert safety.status_code == 200, safety.text
    assert safety.json() == {
        "blocked": True,
        "reason": "Emergency Stop active: Test emergency stop",
        "rule_id": None,
    }

    response = client.post(
        f"/api/v1/digital-twin/devices/{created.json()['id']}/control",
        headers=headers,
        json={"command": "on"},
    )
    assert response.status_code == 423, response.text
    assert "Emergency Stop active" in response.json()["detail"]

    db = test_db()
    try:
        device = db.query(DigitalTwinDevice).filter_by(id=created.json()["id"]).one()
        assert device.state["output"] == "idle"
        assert "command" not in device.state
    finally:
        db.close()


def test_unconfigured_hardware_adapter_fails_without_mutating_device(client, test_db, monkeypatch):
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": "grpc-pump",
        "name": "gRPC Pump",
        "kind": "actuator",
        "device_type": "pump",
        "state": {"output": "idle"},
    })
    assert created.status_code == 200, created.text
    device_id = created.json()["id"]

    configured = client.put(
        f"/api/v1/digital-twin/devices/{device_id}",
        headers=headers,
        json={"adapter_type": "grpc"},
    )
    assert configured.status_code == 200, configured.text
    assert configured.json()["simulation_enabled"] is False

    response = client.post(
        f"/api/v1/digital-twin/devices/{device_id}/control",
        headers=headers,
        json={"command": "on"},
    )
    assert response.status_code == 503, response.text

    db = test_db()
    try:
        device = db.query(DigitalTwinDevice).filter_by(id=device_id).one()
        assert "requested_command" not in device.state
        assert device.state["output"] == "idle"
    finally:
        db.close()


def test_configured_hardware_adapter_uses_common_device_control_route(
    client, test_db, monkeypatch
):
    from types import SimpleNamespace

    from backend.device_adapters import AdapterRegistry, GrpcAdapter

    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    registry = AdapterRegistry()
    registry.register(GrpcAdapter(
        lambda device_id: lambda request: SimpleNamespace(
            accepted=True,
            confirmed=True,
            message="fake hardware acknowledged",
        )
    ))
    monkeypatch.setattr("backend.device_adapters.adapter_registry", registry)
    monkeypatch.setattr("backend.routers.digital_twin.adapter_registry", registry)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": "configured-grpc-pump",
        "name": "Configured gRPC Pump",
        "kind": "actuator",
        "device_type": "pump",
        "adapter_type": "grpc",
        "state": {"output": "idle"},
    })
    assert created.status_code == 200, created.text
    assert created.json()["simulation_enabled"] is False

    response = client.post(
        f"/api/v1/digital-twin/devices/{created.json()['id']}/control",
        headers=headers,
        json={"command": "on"},
    )
    assert response.status_code == 200, response.text
    state = response.json()["state"]
    assert state["requested_command"] == "on"
    assert "command" not in state
    assert state["last_command_delivery"]["confirmed"] is True


def test_device_telemetry_uses_adapter_validation_and_persistent_twin_history(
    client, test_db, monkeypatch
):
    monkeypatch.setattr("backend.routers.digital_twin.SessionLocal", test_db)
    headers = {"Authorization": "Bearer test-token"}
    created = client.post("/api/v1/digital-twin/devices", headers=headers, json={
        "device_id": "temperature-01",
        "name": "Temperature Sensor",
        "kind": "sensor",
        "device_type": "temperature",
    })
    assert created.status_code == 200, created.text
    device_id = created.json()["id"]

    rejected = client.post(
        f"/api/v1/digital-twin/devices/{device_id}/telemetry",
        headers=headers,
        json={"tenant_id": 999, "value": 22, "unit": "C"},
    )
    assert rejected.status_code == 422, rejected.text

    response = client.post(
        f"/api/v1/digital-twin/devices/{device_id}/telemetry",
        headers=headers,
        json={
            "device_id": "temperature-01",
            "tenant_id": 1,
            "zone_id": None,
            "value": 22.5,
            "unit": "C",
            "sensor_type": "temperature",
            "sampled_at": "2026-10-26T12:00:00Z",
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["device"]["state"]["value"] == 22.5

    db = test_db()
    try:
        samples = db.query(DigitalTwinTelemetry).filter_by(device_id=device_id).all()
        assert len(samples) == 1
        assert samples[0].snapshot["state"]["value"] == 22.5
    finally:
        db.close()