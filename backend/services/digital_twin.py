"""Deterministic, database-backed simulation primitives for virtual devices."""
from datetime import datetime
import random

from backend.models.digital_twin import DigitalTwinDevice


DEVICE_KINDS = {"sensor", "robot", "actuator"}

SENSOR_PROFILES = {
    "temperature": {
        "unit": "C", "minimum": 5.0, "maximum": 45.0,
        "warning": (10.0, 35.0), "critical": (5.0, 40.0), "step": 1.2,
    },
    "humidity": {
        "unit": "%", "minimum": 10.0, "maximum": 95.0,
        "warning": (20.0, 90.0), "critical": (10.0, 95.0), "step": 2.5,
    },
    "soil_moisture": {
        "unit": "%", "minimum": 5.0, "maximum": 95.0,
        "warning": (20.0, 80.0), "critical": (10.0, 90.0), "step": 3.0,
    },
    "light": {
        "unit": "lux", "minimum": 0.0, "maximum": 100000.0,
        "warning": (100.0, 90000.0), "critical": (10.0, 100000.0), "step": 250.0,
    },
    "pressure": {
        "unit": "hPa", "minimum": 900.0, "maximum": 1100.0,
        "warning": (950.0, 1050.0), "critical": (920.0, 1080.0), "step": 4.0,
    },
}

DEFAULT_SENSOR_PROFILE = {
    "unit": "%", "minimum": 0.0, "maximum": 100.0,
    "warning": (10.0, 90.0), "critical": (0.0, 100.0), "step": 2.5,
}


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def _sensor_profile(device_type: str) -> dict:
    return SENSOR_PROFILES.get(str(device_type).lower(), DEFAULT_SENSOR_PROFILE)


def _sensor_value(device: DigitalTwinDevice, rng: random.Random) -> float:
    profile = _sensor_profile(device.device_type)
    current = float((device.state or {}).get("value", (profile["minimum"] + profile["maximum"]) / 2))
    return _bounded(current + rng.uniform(-profile["step"], profile["step"]), profile["minimum"], profile["maximum"])


def _reading_assessment(value: float, profile: dict) -> str:
    warning_low, warning_high = profile["warning"]
    critical_low, critical_high = profile["critical"]
    if value < critical_low or value > critical_high:
        return "critical"
    if value < warning_low or value > warning_high:
        return "warning"
    return "normal"


def _condition_matches(value: float, policy: dict) -> bool:
    threshold = float(policy.get("threshold", 0))
    direction = str(policy.get("direction", policy.get("operator", "below"))).lower()
    if direction in {"above", "gt", ">"}:
        return value > threshold
    if direction in {"at_or_above", "gte", ">="}:
        return value >= threshold
    if direction in {"at_or_below", "lte", "<="}:
        return value <= threshold
    return value < threshold


def _apply_automation(devices: list[DigitalTwinDevice], snapshots: list[dict]) -> None:
    """Apply source-sensor policies to automation-mode actuators."""
    by_device_id = {device.device_id: (device, snapshot) for device, snapshot in zip(devices, snapshots)}
    for device, snapshot in zip(devices, snapshots):
        if device.kind != "sensor":
            continue
        reading_status = snapshot["state"].get("reading_status")
        if reading_status in {"warning", "critical"}:
            snapshot["state"]["alert"] = {
                "severity": reading_status,
                "message": f"{device.name} reading is {reading_status}",
                "source_device_id": device.device_id,
            }

    for device, snapshot in zip(devices, snapshots):
        policy = dict(device.automation_policy or {})
        if device.kind != "actuator" or device.control_mode != "automation" or not policy:
            continue

        source_id = policy.get("source_device_id") or policy.get("source_device")
        source = by_device_id.get(str(source_id)) if source_id is not None else None
        if source is None:
            continue
        source_device, source_snapshot = source
        value = source_snapshot["state"].get("value")
        if value is None:
            continue

        matched = _condition_matches(float(value), policy)
        command = policy.get("on_command", policy.get("command", "on")) if matched else policy.get("off_command", "off")
        state = snapshot["state"]
        state["command"] = command
        state["output"] = "active" if str(command).lower() in {"on", "start", "open", "enable"} else "idle"
        state["control_source"] = "automation"
        state["automation"] = {
            "matched": matched,
            "source_device_id": source_device.device_id,
            "source_value": value,
            "direction": policy.get("direction", policy.get("operator", "below")),
            "threshold": policy.get("threshold"),
            "command": command,
        }
        parameters = policy.get("parameters")
        if isinstance(parameters, dict):
            state["automation_parameters"] = parameters


def tick_once(db, tenant_id: int | None = None, rng: random.Random | None = None) -> list[dict]:
    """Advance enabled devices once and return websocket-ready snapshots."""
    generator = rng or random
    query = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.simulation_enabled.is_(True))
    if tenant_id is not None:
        query = query.filter(DigitalTwinDevice.tenant_id == tenant_id)

    now = datetime.utcnow()
    devices = query.order_by(DigitalTwinDevice.id).all()
    snapshots = []
    for device in devices:
        state = dict(device.state or {})
        position = dict(device.position or {"x": 0.0, "y": 0.0, "z": 0.0})
        if device.control_mode == "manual":
            state["control_source"] = "manual"
        elif device.control_mode == "ai":
            state["control_source"] = "ai"
        else:
            state["control_source"] = "automation"

        if device.kind == "sensor" and device.control_mode != "manual":
            profile = _sensor_profile(device.device_type)
            state["value"] = _sensor_value(device, generator)
            state["unit"] = profile["unit"]
            state["reading_status"] = _reading_assessment(state["value"], profile)
            state["thresholds"] = {
                "warning": {"min": profile["warning"][0], "max": profile["warning"][1]},
                "critical": {"min": profile["critical"][0], "max": profile["critical"][1]},
            }
            state["sampled_at"] = now.isoformat()
        elif device.kind == "robot":
            if device.control_mode == "manual":
                state["activity"] = state.get("activity", "stationary")
            else:
                position["x"] = _bounded(float(position.get("x", 0.0)) + generator.uniform(-0.5, 0.5), -1000, 1000)
                position["y"] = _bounded(float(position.get("y", 0.0)) + generator.uniform(-0.5, 0.5), -1000, 1000)
                state["activity"] = state.get("activity", "patrolling")
        else:
            state["output"] = "active" if state.get("command") == "on" else state.get("output", "idle")
        device.state = state
        device.position = position
        device.status = "online"
        device.last_updated = now
        snapshots.append({
            "id": device.id, "device_id": device.device_id, "tenant_id": device.tenant_id,
            "zone_id": device.zone_id, "name": device.name, "kind": device.kind,
            "device_type": device.device_type, "status": device.status,
            "control_mode": device.control_mode,
            "automation_policy": device.automation_policy or {},
            "position": position, "state": state, "last_updated": now.isoformat(),
        })
    _apply_automation(devices, snapshots)
    for snapshot in snapshots:
        alert = snapshot["state"].get("alert")
        if alert:
            snapshot["alert"] = {
                **alert,
                "device_id": snapshot["device_id"],
                "tenant_id": snapshot["tenant_id"],
                "timestamp": snapshot["last_updated"],
            }
    db.commit()
    return snapshots