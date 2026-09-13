"""Deterministic, database-backed simulation primitives for virtual devices."""
from datetime import datetime
import random

from backend.models.digital_twin import DigitalTwinDevice


DEVICE_KINDS = {"sensor", "robot", "actuator"}
_LIVE_UPDATE_COUNTER = 0


def build_predictive_recommendations(devices: list[DigitalTwinDevice]) -> list[dict]:
    """Generate concise, AI-style maintenance recommendations from device state."""
    recommendations = []
    sensors = [device for device in devices if device.kind == "sensor"]
    actuators = [device for device in devices if device.kind == "actuator"]

    for device in sensors:
        state = device.state or {}
        status = state.get("reading_status")
        value = state.get("value")
        if status in {"warning", "critical"}:
            focus = str(device.device_type or "sensor")
            recommendations.append({
                "type": "maintenance",
                "focus": focus,
                "severity": status,
                "message": f"{device.name} requires inspection; current {focus} reading is {status}.",
                "days_until_action": 2 if status == "critical" else 5,
                "confidence": 92 if status == "critical" else 81,
                "value": value,
            })

    for device in actuators:
        state = device.state or {}
        output = state.get("output")
        if output == "active":
            recommendations.append({
                "type": "maintenance",
                "focus": device.device_type or "actuator",
                "severity": "monitor",
                "message": f"{device.name} remains active; verify runtime efficiency during the next inspection window.",
                "days_until_action": 7,
                "confidence": 74,
                "value": output,
            })

    if not recommendations:
        recommendations.append({
            "type": "maintenance",
            "focus": "system",
            "severity": "normal",
            "message": "System health remains within expected operating range; routine monitoring continues.",
            "days_until_action": 14,
            "confidence": 88,
            "value": None,
        })

    return sorted(recommendations, key=lambda item: ({"critical": 0, "warning": 1, "monitor": 2, "normal": 3}.get(item["severity"], 99), item["days_until_action"]))


def build_optimization_recommendations(devices: list[DigitalTwinDevice]) -> list[dict]:
    """Generate AI-style crop, soil, and energy optimization actions."""
    optimizations = []
    sensors = [device for device in devices if device.kind == "sensor"]

    soil_sensors = [
        device for device in sensors
        if (device.device_type or "").lower() in {"soil_moisture", "humidity", "temperature"}
    ]
    energy_sensors = [
        device for device in sensors
        if (device.device_type or "").lower() in {"power", "energy", "battery", "voltage"}
    ]

    for device in soil_sensors:
        state = device.state or {}
        status = state.get("reading_status")
        value = state.get("value")
        if status in {"warning", "critical"}:
            severity = "high" if status == "critical" else "medium"
            action_text = "Reduce irrigation volatility and rebalance nutrient delivery" if (device.device_type or "").lower() == "soil_moisture" else "Shift climate and irrigation timing to stabilize crop conditions"
            optimizations.append({
                "domain": "soil",
                "type": "optimization",
                "focus": str(device.device_type or "soil"),
                "severity": severity,
                "message": f"{device.name} indicates a crop-zone imbalance; {action_text} for the next maintenance window.",
                "confidence": 89 if status == "critical" else 81,
                "value": value,
            })

    for device in energy_sensors:
        state = device.state or {}
        status = state.get("reading_status")
        value = state.get("value")
        if status in {"warning", "critical"} or (isinstance(value, (int, float)) and value >= 80):
            optimizations.append({
                "domain": "energy",
                "type": "optimization",
                "focus": str(device.device_type or "power"),
                "severity": "high" if status == "critical" else "medium",
                "message": f"{device.name} is consuming above the preferred range; shift non-critical loads and recharge reserve capacity during the next solar peak.",
                "confidence": 86,
                "value": value,
            })

    if not optimizations:
        optimizations.append({
            "domain": "system",
            "type": "optimization",
            "focus": "estate",
            "severity": "low",
            "message": "Current soil and energy conditions are within target bands; continue with standard scheduling and routine monitoring.",
            "confidence": 90,
            "value": None,
        })

    return sorted(optimizations, key=lambda item: ({"high": 0, "medium": 1, "low": 2}.get(item["severity"], 99), item["confidence"]), reverse=True)


def build_adaptation_recommendations(devices: list[DigitalTwinDevice]) -> list[dict]:
    """Generate weather and resource adaptation guidance from environmental conditions."""
    adaptations = []
    sensors = [device for device in devices if device.kind == "sensor"]

    weather_sensors = [
        device for device in sensors
        if (device.device_type or "").lower() in {"temperature", "humidity", "soil_temperature", "weather", "pressure"}
    ]
    resource_sensors = [
        device for device in sensors
        if (device.device_type or "").lower() in {"power", "energy", "battery", "voltage", "water"}
    ]

    for device in weather_sensors:
        state = device.state or {}
        status = state.get("reading_status")
        value = state.get("value")
        if status in {"warning", "critical"} or (isinstance(value, (int, float)) and value <= 10):
            adaptations.append({
                "domain": "weather",
                "type": "adaptation",
                "focus": str(device.device_type or "weather"),
                "severity": "high" if status == "critical" else "medium",
                "message": f"{device.name} indicates unstable climate conditions; trigger frost protection, shade response, and irrigation timing adjustments to preserve crop health.",
                "confidence": 90 if status == "critical" else 82,
                "value": value,
            })

    for device in resource_sensors:
        state = device.state or {}
        status = state.get("reading_status")
        value = state.get("value")
        if status in {"warning", "critical"} or (isinstance(value, (int, float)) and value >= 80):
            adaptations.append({
                "domain": "resource",
                "type": "adaptation",
                "focus": str(device.device_type or "resource"),
                "severity": "high" if status == "critical" else "medium",
                "message": f"{device.name} suggests constrained resource availability; reroute load demand, conserve reserve capacity, and reschedule heavy operations for better system resilience.",
                "confidence": 88,
                "value": value,
            })

    if not adaptations:
        adaptations.append({
            "domain": "weather",
            "type": "adaptation",
            "focus": "estate",
            "severity": "low",
            "message": "Environmental and resource conditions remain stable; continue with standard operating rhythms and routine adaptation monitoring.",
            "confidence": 90,
            "value": None,
        })

    return sorted(adaptations, key=lambda item: ({"high": 0, "medium": 1, "low": 2}.get(item["severity"], 99), item["confidence"]), reverse=True)


def build_recommendation_summary(*recommendation_sets: list[dict]) -> dict:
    """Summarize all recommendation payloads into a concise executive view."""
    combined = []
    for recommendation_set in recommendation_sets:
        if isinstance(recommendation_set, list):
            combined.extend(recommendation_set)

    by_domain: dict[str, int] = {}
    by_type: dict[str, int] = {}
    top_actions: list[str] = []
    highest_severity = "normal"

    for item in combined:
        domain = str(item.get("domain") or item.get("focus") or "system")
        rec_type = str(item.get("type") or item.get("domain") or "recommendation")
        by_domain[domain] = by_domain.get(domain, 0) + 1
        by_type[rec_type] = by_type.get(rec_type, 0) + 1

        message = str(item.get("message") or item.get("focus") or "Review system status")
        if message and message not in top_actions:
            top_actions.append(message)

        severity = str(item.get("severity") or "normal").lower()
        if severity in {"critical", "high"}:
            highest_severity = "critical"
        elif severity in {"warning", "medium"} and highest_severity != "critical":
            highest_severity = "warning"

    return {
        "total": len(combined),
        "by_domain": by_domain,
        "by_type": by_type,
        "highest_severity": highest_severity,
        "top_actions": top_actions[:5],
    }


def build_alert_summary(devices: list[DigitalTwinDevice]) -> dict:
    """Summarize the current abnormal sensor conditions for quick operator insight."""
    alerts = []
    by_severity: dict[str, int] = {"critical": 0, "warning": 0, "normal": 0}

    for device in devices:
        state = device.state or {}
        status = str(state.get("reading_status") or "normal").lower()
        if status not in {"warning", "critical"}:
            continue
        by_severity[status] = by_severity.get(status, 0) + 1
        alerts.append({
            "device": device.name,
            "type": str(device.device_type or "sensor"),
            "severity": status,
            "message": f"{device.name} is reporting a {status} reading.",
        })

    return {
        "total": len(alerts),
        "by_severity": by_severity,
        "highest_severity": "critical" if by_severity["critical"] else "warning" if by_severity["warning"] else "normal",
        "top_alerts": [alert["message"] for alert in alerts[:5]],
    }


def build_workflow_summary(
    recommendations: list[dict],
    optimization: list[dict],
    adaptation: list[dict],
    health_score: int = 100,
    alert_summary: dict | None = None,
    stability: dict | None = None,
) -> dict:
    """Aggregate the core digital-twin intelligence modules into a single workflow view."""
    modules = {
        "predictive": {"count": len(recommendations or []), "status": "active" if recommendations else "idle"},
        "optimization": {"count": len(optimization or []), "status": "active" if optimization else "idle"},
        "adaptation": {"count": len(adaptation or []), "status": "active" if adaptation else "idle"},
        "alerts": {
            "count": int((alert_summary or {}).get("total", 0)),
            "status": "watch" if (alert_summary or {}).get("total", 0) else "clear",
        },
    }
    status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "critical"
    summary_parts = []
    if recommendations:
        summary_parts.append("Predictive maintenance is active.")
    if optimization:
        summary_parts.append("Optimization rules are balancing soil and energy loads.")
    if adaptation:
        summary_parts.append("Weather and resource adaptation is managing environmental shifts.")
    if not summary_parts:
        summary_parts.append("The digital twin is online and ready for live operations.")

    return {
        "status": status,
        "summary": " ".join(summary_parts),
        "modules": modules,
        "stability_status": (stability or {}).get("status", "stable"),
    }


def build_api_status(health_score: int, devices: list[DigitalTwinDevice], alert_summary: dict | None = None) -> dict:
    """Surface the runtime API state, last-known errors, and service health."""
    errors = []
    if alert_summary and alert_summary.get("total", 0):
        errors.append("Active operational alerts require review.")
    if health_score < 50:
        errors.append("Runtime health is critical.")
    elif health_score < 80:
        errors.append("Runtime health is degraded.")
    if not devices:
        errors.append("No digital-twin devices are currently configured.")

    if health_score < 50 or not devices or (alert_summary or {}).get("total", 0) >= 3:
        status = "critical"
    elif errors:
        status = "degraded"
    else:
        status = "ok"

    return {
        "status": status,
        "health_score": health_score,
        "errors": errors,
        "devices_monitored": len(devices),
    }


def build_session_summary(tenant_id: int | None = None, active: bool = True) -> dict:
    """Summarize the current authenticated operator session for UI and backend observability."""
    return {
        "tenant_id": tenant_id,
        "active": bool(active),
        "status": "active" if active else "expired",
    }


def build_interaction_summary(devices: list[DigitalTwinDevice]) -> dict:
    """Summarize how the active estate systems are coordinating under the current tenant session."""
    if not devices:
        return {
            "status": "idle",
            "coordinated": False,
            "system_count": 0,
            "systems": [],
            "active_users": 0,
            "tenant_scope": "none",
        }

    system_map = {
        "temperature": "climate",
        "humidity": "climate",
        "pressure": "climate",
        "soil_moisture": "soil",
        "water": "water",
        "power": "energy",
        "energy": "energy",
        "battery": "energy",
        "voltage": "energy",
    }

    systems = []
    for device in devices:
        system_name = system_map.get(str(device.device_type or "").lower(), "operations")
        if system_name not in systems:
            systems.append(system_name)

    coordinated = len(systems) >= 2
    status = "coordinated" if coordinated else "stable"
    if any(str((device.state or {}).get("reading_status") or "normal").lower() in {"warning", "critical"} for device in devices):
        status = "degraded" if coordinated else "watch"

    return {
        "status": status,
        "coordinated": coordinated,
        "system_count": len(systems),
        "systems": systems,
        "active_users": 1,
        "tenant_scope": "single-tenant",
    }


def build_stability_summary(devices: list[DigitalTwinDevice], updates_processed: int | None = None) -> dict:
    """Track whether repeated live updates are remaining stable and report a quick summary."""
    global _LIVE_UPDATE_COUNTER
    if updates_processed is None:
        updates_processed = _LIVE_UPDATE_COUNTER

    alert_count = sum(1 for device in devices if str((device.state or {}).get("reading_status") or "normal").lower() in {"warning", "critical"})
    stable = bool(devices) and updates_processed >= 1 and alert_count <= len(devices)
    return {
        "stable": stable,
        "updates_processed": updates_processed,
        "devices_monitored": len(devices),
        "active_alerts": alert_count,
        "status": "stable" if stable else "degraded",
    }

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
    global _LIVE_UPDATE_COUNTER
    generator = rng or random
    query = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.simulation_enabled.is_(True))
    if tenant_id is not None:
        query = query.filter(DigitalTwinDevice.tenant_id == tenant_id)

    now = datetime.utcnow()
    devices = query.order_by(DigitalTwinDevice.id).all()
    snapshots = []
    _LIVE_UPDATE_COUNTER += 1

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