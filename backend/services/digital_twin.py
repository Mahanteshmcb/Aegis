"""Deterministic, database-backed simulation primitives for virtual devices."""
from datetime import datetime
import random

from backend.models.digital_twin import DigitalTwinDevice


DEVICE_KINDS = {"sensor", "robot", "actuator"}


def _bounded(value: float, minimum: float, maximum: float) -> float:
    return round(max(minimum, min(maximum, value)), 2)


def _sensor_value(device: DigitalTwinDevice, rng: random.Random) -> float:
    current = float((device.state or {}).get("value", 50.0))
    if device.device_type == "temperature":
        minimum, maximum = 10.0, 40.0
    elif device.device_type == "humidity":
        minimum, maximum = 20.0, 95.0
    else:
        minimum, maximum = 0.0, 100.0
    return _bounded(current + rng.uniform(-2.5, 2.5), minimum, maximum)


def tick_once(db, tenant_id: int | None = None, rng: random.Random | None = None) -> list[dict]:
    """Advance enabled devices once and return websocket-ready snapshots."""
    generator = rng or random
    query = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.simulation_enabled.is_(True))
    if tenant_id is not None:
        query = query.filter(DigitalTwinDevice.tenant_id == tenant_id)

    now = datetime.utcnow()
    snapshots = []
    for device in query.order_by(DigitalTwinDevice.id).all():
        state = dict(device.state or {})
        position = dict(device.position or {"x": 0.0, "y": 0.0, "z": 0.0})
        if device.control_mode == "manual":
            state["control_source"] = "manual"
        elif device.control_mode == "ai":
            state["control_source"] = "ai"
        else:
            state["control_source"] = "automation"

        if device.kind == "sensor" and device.control_mode != "manual":
            state["value"] = _sensor_value(device, generator)
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
    db.commit()
    return snapshots