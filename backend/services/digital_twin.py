"""Deterministic, database-backed simulation primitives for virtual devices."""
from datetime import datetime
import hashlib
import json
import math
import random
from uuid import uuid4

from backend.models.digital_twin import DigitalTwinDevice
from backend.models_db import AuditLog, DigitalTwinTelemetry


DEVICE_KINDS = {"sensor", "robot", "actuator"}
_LIVE_UPDATE_COUNTER = 0


def _stage_system_audit(
    db,
    tenant_id: int,
    event_type: str,
    entity_type: str,
    entity_id: str,
    details: dict,
) -> None:
    metadata = {
        **details,
        "action": event_type,
        "actor_user_id": None,
        "actor_email": "system@aegis.local",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "outcome": "success",
    }
    serialized = json.dumps(metadata, sort_keys=True, default=str)
    db.add(AuditLog(
        tenant_id=tenant_id,
        event_type=event_type,
        data_hash=hashlib.sha256(serialized.encode()).hexdigest(),
        actor_email="system@aegis.local",
        action=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        outcome="success",
        details=metadata,
    ))


def _stage_alert_transition_audit(db, snapshot: dict, previous_alert: dict | None) -> None:
    alert = snapshot.get("alert")
    cleared = snapshot.get("alert_cleared")
    if alert and not previous_alert:
        event_type = "digital_twin.alert_started"
        details = {
            "severity": alert.get("severity"),
            "message": alert.get("message"),
            "event_id": alert.get("event_id"),
            "device_id": snapshot["device_id"],
        }
    elif alert and previous_alert and alert.get("severity") != previous_alert.get("severity"):
        event_type = "digital_twin.alert_escalated"
        details = {
            "previous_severity": previous_alert.get("severity"),
            "severity": alert.get("severity"),
            "message": alert.get("message"),
            "event_id": alert.get("event_id"),
            "device_id": snapshot["device_id"],
        }
    elif cleared:
        event_type = "digital_twin.alert_recovered"
        details = {
            "severity": cleared.get("severity"),
            "message": cleared.get("message"),
            "event_id": cleared.get("event_id"),
            "device_id": snapshot["device_id"],
        }
    else:
        return

    _stage_system_audit(
        db,
        snapshot["tenant_id"],
        event_type,
        "digital_twin_device",
        str(snapshot["id"]),
        details,
    )


def _stage_automation_transition_audit(
    db,
    snapshot: dict,
    previous_state: dict | None,
) -> None:
    state = snapshot["state"]
    if (
        snapshot["kind"] != "actuator"
        or snapshot["control_mode"] != "automation"
        or previous_state is None
        or (
            state.get("command") == previous_state.get("command")
            and state.get("output") == previous_state.get("output")
        )
    ):
        return
    automation = state.get("automation") or {}
    _stage_system_audit(
        db,
        snapshot["tenant_id"],
        "digital_twin.automation_actuated",
        "digital_twin_device",
        str(snapshot["id"]),
        {
            "device_id": snapshot["device_id"],
            "previous_command": previous_state.get("command"),
            "command": state.get("command"),
            "previous_output": previous_state.get("output"),
            "output": state.get("output"),
            "source_device_id": automation.get("source_device_id"),
            "source_value": automation.get("source_value"),
            "direction": automation.get("direction"),
            "threshold": automation.get("threshold"),
            "matched": automation.get("matched"),
        },
    )


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
    "structural_displacement": {
        "unit": "mm", "minimum": -100.0, "maximum": 100.0,
        "warning": (-20.0, 20.0), "critical": (-50.0, 50.0), "step": 0.0,
    },
    "solar_generation": {
        "unit": "kW", "minimum": 0.0, "maximum": 8.0,
        "warning": (0.0, 7.0), "critical": (0.0, 8.0), "step": 0.4,
    },
    "energy_consumption": {
        "unit": "kW", "minimum": 0.0, "maximum": 10.0,
        "warning": (0.0, 8.0), "critical": (0.0, 10.0), "step": 0.35,
    },
    "battery_soc": {
        "unit": "%", "minimum": 0.0, "maximum": 100.0,
        "warning": (15.0, 90.0), "critical": (5.0, 98.0), "step": 1.5,
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


def _soil_moisture_step(
    device: DigitalTwinDevice,
    devices: list[DigitalTwinDevice],
    step_seconds: float,
) -> tuple[float, dict]:
    state = device.state or {}
    model = state.get("simulation_model") or {}
    if not isinstance(model, dict):
        raise ValueError(f"Invalid soil-moisture simulation model for {device.device_id}")

    current = float(state.get("value", 50.0))
    drainage_rate = float(model.get("drainage_rate_per_minute", 0.2))
    infiltration_rate = float(model.get("infiltration_rate_per_minute", 0.03))
    if not all(math.isfinite(value) and value >= 0 for value in (current, drainage_rate, infiltration_rate)):
        raise ValueError(f"Invalid soil-moisture simulation parameters for {device.device_id}")

    irrigation_flow = 0.0
    contributing_actuators = []
    if device.zone_id is not None:
        for actuator in devices:
            if (
                actuator.tenant_id != device.tenant_id
                or actuator.zone_id != device.zone_id
                or actuator.kind != "actuator"
                or actuator.status.lower() != "online"
                or (actuator.device_type or "").lower() not in {
                    "pump", "irrigation_pump", "irrigation_valve", "valve",
                }
            ):
                continue
            actuator_state = actuator.state or {}
            output = str(actuator_state.get("output", "")).lower()
            command = str(actuator_state.get("command", "")).lower()
            if output != "active" and command not in {"on", "open", "start", "enable"}:
                continue
            flow = float(
                actuator_state.get(
                    "flow",
                    actuator_state.get("flow_rate", actuator_state.get("flow_lpm", 1.0)),
                )
            )
            if not math.isfinite(flow) or flow < 0:
                raise ValueError(f"Invalid irrigation flow for {actuator.device_id}")
            irrigation_flow += flow
            contributing_actuators.append(actuator.device_id)

    delta_minutes = step_seconds / 60.0
    next_value = current + (
        infiltration_rate * irrigation_flow - drainage_rate
    ) * delta_minutes
    profile = _sensor_profile(device.device_type)
    details = {
        "model": "soil_moisture_water_balance",
        "assumption": "generic_uncalibrated_demo_parameters",
        "step_seconds": step_seconds,
        "drainage_rate_per_minute": drainage_rate,
        "infiltration_rate_per_minute": infiltration_rate,
        "irrigation_flow": irrigation_flow,
        "contributing_actuators": contributing_actuators,
    }
    next_value = max(profile["minimum"], min(profile["maximum"], next_value))
    return round(next_value, 4), details


def _environment_step(
    device: DigitalTwinDevice,
    devices: list[DigitalTwinDevice],
    step_seconds: float,
) -> tuple[float, dict] | None:
    state = device.state or {}
    device_type = str(device.device_type or "").lower()
    if device_type not in {"temperature", "humidity"}:
        return None
    model = state.get("simulation_model")
    if model is None:
        model = {}
    if not isinstance(model, dict):
        raise ValueError(f"Invalid environmental simulation model for {device.device_id}")
    if model.get("kind") not in {None, "thermal_rc"}:
        raise ValueError(f"Unsupported environmental simulation model for {device.device_id}")

    temperature = device_type == "temperature"
    ambient_key = "ambient_temperature_c" if temperature else "ambient_humidity_percent"
    effect_key = "thermal_effect_c_per_minute" if temperature else "humidity_effect_percent_per_minute"
    ambient_default = 20.0 if temperature else 55.0
    minimum, maximum = _sensor_profile(device.device_type)["minimum"], _sensor_profile(device.device_type)["maximum"]
    current = float(state.get("value", ambient_default))
    ambient = float(model.get(ambient_key, ambient_default))
    time_constant = float(model.get("time_constant_seconds", 900.0 if temperature else 1800.0))
    if not all(math.isfinite(value) for value in (current, ambient, time_constant)) or time_constant <= 0:
        raise ValueError(f"Invalid environmental simulation parameters for {device.device_id}")

    exchange_per_second = 1.0 / time_constant
    effect_per_minute = 0.0
    contributing_actuators = []
    if device.zone_id is not None:
        for actuator in devices:
            if (
                actuator.tenant_id != device.tenant_id
                or actuator.zone_id != device.zone_id
                or actuator.kind != "actuator"
                or actuator.status.lower() != "online"
            ):
                continue
            actuator_state = actuator.state or {}
            output = str(actuator_state.get("output", "")).lower()
            command = str(actuator_state.get("command", "")).lower()
            if output != "active" and command not in {"on", "open", "start", "enable"}:
                continue
            actuator_model = actuator_state.get("simulation_model") or {}
            if not isinstance(actuator_model, dict):
                raise ValueError(f"Invalid actuator simulation model for {actuator.device_id}")
            effect = float(actuator_model.get(effect_key, actuator_state.get(effect_key, 0.0)))
            exchange = float(actuator_model.get("air_exchange_per_second", 0.0))
            if not math.isfinite(effect) or not math.isfinite(exchange) or exchange < 0:
                raise ValueError(f"Invalid environmental actuator parameters for {actuator.device_id}")
            effect_per_minute += effect
            exchange_per_second += exchange
            if effect or exchange:
                contributing_actuators.append(actuator.device_id)

    exchange_fraction = 1.0 - math.exp(-exchange_per_second * step_seconds)
    next_value = current + (ambient - current) * exchange_fraction
    next_value += effect_per_minute * step_seconds / 60.0
    details = {
        "model": "first_order_environment_demo",
        "assumption": "generic_uncalibrated_demo_parameters",
        "step_seconds": step_seconds,
        "ambient_value": ambient,
        "time_constant_seconds": time_constant,
        "actuator_effect_per_minute": effect_per_minute,
        "contributing_actuators": contributing_actuators,
    }
    return _bounded(next_value, minimum, maximum), details


def _water_level_step(
    device: DigitalTwinDevice,
    devices: list[DigitalTwinDevice],
    step_seconds: float,
) -> tuple[float, dict] | None:
    state = device.state or {}
    if str(device.device_type or "").lower() not in {"water_level", "tank_level", "water_tank"}:
        return None
    model = state.get("simulation_model")
    if model is None:
        return None
    if not isinstance(model, dict):
        raise ValueError(f"Invalid water-tank simulation model for {device.device_id}")
    if model.get("kind") != "water_tank":
        raise ValueError(f"Unsupported water-tank simulation model for {device.device_id}")

    capacity_liters = float(model.get("capacity_liters", 1000.0))
    current_percent = float(state.get("value", 50.0))
    inflow_lpm = float(model.get("inflow_lpm", 0.0))
    outflow_lpm = float(model.get("outflow_lpm", 0.0))
    if (
        not all(math.isfinite(value) for value in (capacity_liters, current_percent, inflow_lpm, outflow_lpm))
        or capacity_liters <= 0
        or not 0 <= current_percent <= 100
        or inflow_lpm < 0
        or outflow_lpm < 0
    ):
        raise ValueError(f"Invalid water-tank simulation parameters for {device.device_id}")

    contributors = []
    if device.zone_id is not None:
        for actuator in devices:
            if (
                actuator.tenant_id != device.tenant_id
                or actuator.zone_id != device.zone_id
                or actuator.kind != "actuator"
                or actuator.status.lower() != "online"
            ):
                continue
            actuator_state = actuator.state or {}
            output = str(actuator_state.get("output", "")).lower()
            command = str(actuator_state.get("command", "")).lower()
            if output != "active" and command not in {"on", "open", "start", "enable"}:
                continue
            actuator_model = actuator_state.get("simulation_model") or {}
            if not isinstance(actuator_model, dict):
                raise ValueError(f"Invalid actuator simulation model for {actuator.device_id}")
            direction = str(actuator_model.get("flow_direction", "")).lower()
            if direction not in {"inflow", "outflow"}:
                continue
            flow = float(actuator_model.get("flow_lpm", actuator_state.get("flow_lpm", 0.0)))
            if not math.isfinite(flow) or flow < 0:
                raise ValueError(f"Invalid water flow for {actuator.device_id}")
            if direction == "inflow":
                inflow_lpm += flow
            else:
                outflow_lpm += flow
            contributors.append(actuator.device_id)

    current_liters = capacity_liters * current_percent / 100.0
    next_liters = current_liters + (inflow_lpm - outflow_lpm) * step_seconds / 60.0
    next_percent = _bounded(next_liters * 100.0 / capacity_liters, 0.0, 100.0)
    return next_percent, {
        "model": "water_tank_mass_balance_demo",
        "assumption": "generic_uncalibrated_demo_parameters",
        "step_seconds": step_seconds,
        "capacity_liters": capacity_liters,
        "inflow_lpm": inflow_lpm,
        "outflow_lpm": outflow_lpm,
        "contributing_actuators": contributors,
    }


def _structural_step(
    device: DigitalTwinDevice,
    state: dict,
    step_seconds: float,
) -> tuple[float, dict, dict] | None:
    if str(device.device_type or "").lower() != "structural_displacement":
        return None
    model = state.get("simulation_model") or {}
    if not isinstance(model, dict):
        raise ValueError(f"Invalid structural simulation model for {device.device_id}")
    if model.get("kind") != "single_degree_of_freedom":
        raise ValueError(f"Unsupported structural simulation model for {device.device_id}")

    mass_kg = float(model.get("mass_kg", 100.0))
    natural_frequency_hz = float(model.get("natural_frequency_hz", 1.0))
    damping_ratio = float(model.get("damping_ratio", 0.05))
    force_newtons = float(model.get("force_newtons", 0.0))
    simulation_state = state.get("simulation_state") or {}
    if not isinstance(simulation_state, dict):
        raise ValueError(f"Invalid structural simulation state for {device.device_id}")
    displacement_m = float(simulation_state.get("displacement_m", 0.0))
    velocity_m_per_second = float(simulation_state.get("velocity_m_per_second", 0.0))
    parameters = (
        mass_kg,
        natural_frequency_hz,
        damping_ratio,
        force_newtons,
        displacement_m,
        velocity_m_per_second,
    )
    if (
        not all(math.isfinite(value) for value in parameters)
        or mass_kg <= 0
        or natural_frequency_hz <= 0
        or damping_ratio < 0
    ):
        raise ValueError(f"Invalid structural simulation parameters for {device.device_id}")

    angular_frequency = 2.0 * math.pi * natural_frequency_hz
    stiffness = mass_kg * angular_frequency * angular_frequency
    damping = 2.0 * damping_ratio * mass_kg * angular_frequency
    substep_count = max(1, math.ceil(step_seconds * angular_frequency))
    if substep_count > 10000:
        raise ValueError(f"Structural simulation step is too large for {device.device_id}")
    substep_seconds = step_seconds / substep_count
    for _ in range(substep_count):
        acceleration = (
            force_newtons - damping * velocity_m_per_second - stiffness * displacement_m
        ) / mass_kg
        velocity_m_per_second += acceleration * substep_seconds
        displacement_m += velocity_m_per_second * substep_seconds

    return round(displacement_m * 1000.0, 4), {
        "model": "single_degree_of_freedom_structure_demo",
        "assumption": "generic_uncalibrated_demo_parameters",
        "mass_kg": mass_kg,
        "natural_frequency_hz": natural_frequency_hz,
        "damping_ratio": damping_ratio,
        "force_newtons": force_newtons,
        "step_seconds": step_seconds,
        "integration_substeps": substep_count,
    }, {
            "displacement_m": displacement_m,
            "velocity_m_per_second": velocity_m_per_second,
    }


def _robot_step(
    device: DigitalTwinDevice,
    devices: list[DigitalTwinDevice],
    position: dict,
    state: dict,
    step_seconds: float,
) -> tuple[dict, dict]:
    model = state.get("simulation_model")
    if model is None:
        model = {}
    if not isinstance(model, dict):
        raise ValueError(f"Invalid robot simulation model for {device.device_id}")
    if model.get("kind") not in {None, "robot_kinematics"}:
        raise ValueError(f"Unsupported robot simulation model for {device.device_id}")

    next_position = dict(position)
    target = state.get("navigation_target")
    command = str(state.get("command", "")).lower()
    speed = float(model.get("max_speed_units_per_second", 1.0))
    if not math.isfinite(speed) or speed < 0:
        raise ValueError(f"Invalid robot speed for {device.device_id}")
    if isinstance(target, dict) and command not in {"stop", "off"} and state.get("activity") != "stopped":
        axes = ("x", "y", "z")
        current = [float(position.get(axis, 0.0)) for axis in axes]
        destination = [float(target.get(axis, current[index])) for index, axis in enumerate(axes)]
        if not all(math.isfinite(value) for value in (*current, *destination)):
            raise ValueError(f"Invalid robot position or target for {device.device_id}")
        distances = [destination[index] - current[index] for index in range(3)]
        distance = math.sqrt(sum(delta * delta for delta in distances))
        travel = min(distance, speed * step_seconds)
        if distance > 0:
            next_position = {
                axis: round(current[index] + distances[index] * travel / distance, 4)
                for index, axis in enumerate(axes)
            }
        if distance <= speed * step_seconds:
            state.pop("navigation_target", None)
            state["activity"] = "stationary"
        else:
            state["activity"] = "moving"

    battery_key = "battery_percent" if "battery_percent" in state else "battery" if "battery" in state else None
    if battery_key is not None:
        capacity_wh = float(model.get("battery_capacity_wh", 600.0))
        load_key = "moving_load_w" if state.get("activity") == "moving" else "idle_load_w"
        load_w = float(model.get(load_key, 90.0 if load_key == "moving_load_w" else 12.0))
        charging_w = 0.0
        for actuator in devices:
            if (
                actuator.tenant_id != device.tenant_id
                or actuator.zone_id != device.zone_id
                or actuator.kind != "actuator"
                or actuator.status.lower() != "online"
            ):
                continue
            actuator_state = actuator.state or {}
            active = str(actuator_state.get("output", "")).lower() == "active"
            active = active or str(actuator_state.get("command", "")).lower() in {"on", "start", "enable"}
            if not active:
                continue
            actuator_model = actuator_state.get("simulation_model") or {}
            if isinstance(actuator_model, dict) and actuator_model.get("kind") == "robot_charger":
                charging_w += float(actuator_model.get("charging_power_w", 0.0))
        battery = float(state[battery_key])
        if (
            not all(math.isfinite(value) for value in (capacity_wh, load_w, charging_w, battery))
            or capacity_wh <= 0
            or load_w < 0
            or charging_w < 0
            or not 0 <= battery <= 100
        ):
            raise ValueError(f"Invalid robot energy simulation parameters for {device.device_id}")
        state[battery_key] = round(
            max(
                0.0,
                min(100.0, battery + (charging_w - load_w) * step_seconds / (capacity_wh * 36.0)),
            ),
            6,
        )
        state["energy_simulation"] = {
            "model": "robot_energy_balance_demo",
            "assumption": "generic_uncalibrated_demo_parameters",
            "capacity_wh": capacity_wh,
            "load_w": load_w,
            "charging_power_w": charging_w,
            "step_seconds": step_seconds,
        }
    state["simulation"] = {
        "model": "robot_point_kinematics_demo",
        "assumption": "scene_units_are_not_surveyed_meters",
        "max_speed_units_per_second": speed,
        "step_seconds": step_seconds,
    }
    return next_position, state


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
    by_device_id = {
        (device.tenant_id, device.device_id): (device, snapshot)
        for device, snapshot in zip(devices, snapshots)
    }
    for device, snapshot in zip(devices, snapshots):
        policy = dict(device.automation_policy or {})
        if (
            device.kind != "actuator"
            or device.control_mode != "automation"
            or not policy
            or device.status.lower() != "online"
        ):
            continue

        source_id = policy.get("source_device_id") or policy.get("source_device")
        source = by_device_id.get((device.tenant_id, str(source_id))) if source_id is not None else None
        if source is None:
            continue
        source_device, source_snapshot = source
        if source_device.status.lower() != "online":
            snapshot["state"]["automation"] = {
                "matched": False,
                "source_device_id": source_device.device_id,
                "blocked_reason": "source_device_unavailable",
                "command": snapshot["state"].get("command"),
            }
            continue
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


def _apply_alert_transition(snapshot: dict, previous_alert: dict | None) -> None:
    if snapshot["kind"] != "sensor" or snapshot["status"].lower() != "online":
        return
    state = snapshot["state"]
    reading_status = state.get("reading_status")
    if reading_status in {"warning", "critical"}:
        severity_rank = {"warning": 1, "critical": 2}
        if previous_alert:
            alert_event = dict(previous_alert)
            if severity_rank.get(reading_status, 0) > severity_rank.get(alert_event.get("severity"), 0):
                alert_event["severity"] = reading_status
                alert_event["message"] = f"{snapshot['name']} reading is {reading_status}"
                state["alert"] = alert_event
                snapshot["alert"] = {
                    **alert_event,
                    "device_id": snapshot["device_id"],
                    "tenant_id": snapshot["tenant_id"],
                    "timestamp": snapshot["last_updated"],
                }
        else:
            alert_event = {
                "event_id": str(uuid4()),
                "severity": reading_status,
                "message": f"{snapshot['name']} reading is {reading_status}",
                "source_device_id": snapshot["device_id"],
                "started_at": snapshot["last_updated"],
            }
            state["alert"] = alert_event
            snapshot["alert"] = {
                **alert_event,
                "device_id": snapshot["device_id"],
                "tenant_id": snapshot["tenant_id"],
                "timestamp": snapshot["last_updated"],
            }
    elif previous_alert:
        state.pop("alert", None)
        snapshot["alert_cleared"] = {
            "event_id": previous_alert.get("event_id"),
            "device_id": snapshot["device_id"],
            "tenant_id": snapshot["tenant_id"],
            "severity": previous_alert.get("severity"),
            "message": f"{snapshot['name']} returned to normal",
            "timestamp": snapshot["last_updated"],
        }


def ingest_sensor_sample(
    db,
    device: DigitalTwinDevice,
    value: float,
    unit: str,
    sampled_at: datetime,
) -> list[dict]:
    """Persist a physical sensor sample through the canonical twin and telemetry model."""
    if device.kind != "sensor":
        raise ValueError("Physical telemetry can only be ingested for sensor devices")
    profile = _sensor_profile(device.device_type)
    state = dict(device.state or {})
    previous_alert = dict(state.get("alert") or {})
    state.update({
        "value": float(value),
        "unit": unit or profile["unit"],
        "sampled_at": sampled_at.isoformat(),
        "reading_status": _reading_assessment(float(value), profile),
        "thresholds": {
            "warning": {"min": profile["warning"][0], "max": profile["warning"][1]},
            "critical": {"min": profile["critical"][0], "max": profile["critical"][1]},
        },
    })
    device.state = state
    device.status = "online"
    device.simulation_enabled = False
    device.last_updated = sampled_at
    snapshot = {
        "id": device.id,
        "device_id": device.device_id,
        "tenant_id": device.tenant_id,
        "zone_id": device.zone_id,
        "name": device.name,
        "kind": device.kind,
        "device_type": device.device_type,
        "adapter_type": device.adapter_type,
        "status": device.status,
        "control_mode": device.control_mode,
        "automation_policy": device.automation_policy or {},
        "position": device.position or {"x": 0.0, "y": 0.0, "z": 0.0},
        "state": state,
        "last_updated": sampled_at.isoformat(),
    }
    _apply_alert_transition(snapshot, previous_alert)
    _stage_alert_transition_audit(db, snapshot, previous_alert)
    db.add(device)
    devices = db.query(DigitalTwinDevice).filter(
        DigitalTwinDevice.tenant_id == device.tenant_id,
    ).order_by(DigitalTwinDevice.id).all()
    snapshots = []
    previous_actuator_states = {}
    for twin_device in devices:
        if twin_device.id == device.id:
            snapshots.append(snapshot)
            continue
        twin_state = dict(twin_device.state or {})
        if twin_device.kind == "actuator":
            previous_actuator_states[twin_device.id] = dict(twin_state)
        snapshots.append({
            "id": twin_device.id,
            "device_id": twin_device.device_id,
            "tenant_id": twin_device.tenant_id,
            "zone_id": twin_device.zone_id,
            "name": twin_device.name,
            "kind": twin_device.kind,
            "device_type": twin_device.device_type,
            "adapter_type": twin_device.adapter_type,
            "status": twin_device.status,
            "control_mode": twin_device.control_mode,
            "automation_policy": twin_device.automation_policy or {},
            "position": twin_device.position or {"x": 0.0, "y": 0.0, "z": 0.0},
            "state": twin_state,
            "last_updated": twin_device.last_updated.isoformat() if twin_device.last_updated else sampled_at.isoformat(),
        })
    _apply_automation(devices, snapshots)
    for actuator_snapshot in snapshots:
        _stage_automation_transition_audit(
            db,
            actuator_snapshot,
            previous_actuator_states.get(actuator_snapshot["id"]),
        )
    changed_snapshots = [snapshot]
    devices_by_id = {twin_device.id: twin_device for twin_device in devices}
    for actuator_snapshot in snapshots:
        if actuator_snapshot["kind"] != "actuator":
            continue
        actuator = devices_by_id[actuator_snapshot["id"]]
        if actuator_snapshot["state"] == previous_actuator_states.get(actuator.id):
            continue
        actuator.state = actuator_snapshot["state"]
        actuator.last_updated = sampled_at
        actuator_snapshot["last_updated"] = sampled_at.isoformat()
        changed_snapshots.append(actuator_snapshot)
        db.add(DigitalTwinTelemetry(
            tenant_id=actuator.tenant_id,
            device_id=actuator.id,
            snapshot=actuator_snapshot,
            recorded_at=sampled_at,
        ))
    db.add(DigitalTwinTelemetry(
        tenant_id=device.tenant_id,
        device_id=device.id,
        snapshot=snapshot,
        recorded_at=sampled_at,
    ))
    db.commit()
    return changed_snapshots


def tick_once(
    db,
    tenant_id: int | None = None,
    rng: random.Random | None = None,
    step_seconds: float = 1.0,
) -> list[dict]:
    """Advance enabled devices once and return websocket-ready snapshots."""
    global _LIVE_UPDATE_COUNTER
    if not math.isfinite(step_seconds) or step_seconds <= 0:
        raise ValueError("Simulation step_seconds must be a finite positive number")
    generator = rng or random
    query = db.query(DigitalTwinDevice).filter(
        DigitalTwinDevice.simulation_enabled.is_(True),
        DigitalTwinDevice.adapter_type == "simulation",
    )
    if tenant_id is not None:
        query = query.filter(DigitalTwinDevice.tenant_id == tenant_id)

    now = datetime.utcnow()
    devices = query.order_by(DigitalTwinDevice.id).all()
    snapshots = []
    previous_alerts = {
        device.id: dict((device.state or {}).get("alert") or {})
        for device in devices
        if device.kind == "sensor"
    }
    previous_actuator_states = {
        device.id: dict(device.state or {})
        for device in devices
        if device.kind == "actuator"
    }
    _LIVE_UPDATE_COUNTER += 1

    for device in devices:
        state = dict(device.state or {})
        position = dict(device.position or {"x": 0.0, "y": 0.0, "z": 0.0})
        available = device.status.lower() == "online"
        if device.control_mode == "manual":
            state["control_source"] = "manual"
        elif device.control_mode == "ai":
            state["control_source"] = "ai"
        else:
            state["control_source"] = "automation"

        if available and device.kind == "sensor" and device.control_mode != "manual":
            profile = _sensor_profile(device.device_type)
            if (device.device_type or "").lower() == "soil_moisture":
                state["value"], state["simulation"] = _soil_moisture_step(device, devices, step_seconds)
            else:
                structural_result = _structural_step(device, state, step_seconds)
                environment_result = _environment_step(device, devices, step_seconds)
                water_result = _water_level_step(device, devices, step_seconds)
                if structural_result is not None:
                    state["value"], state["simulation"], state["simulation_state"] = structural_result
                elif environment_result is not None:
                    state["value"], state["simulation"] = environment_result
                elif water_result is not None:
                    state["value"], state["simulation"] = water_result
                else:
                    state["value"] = _sensor_value(device, generator)
            state["unit"] = profile["unit"]
            state["reading_status"] = _reading_assessment(state["value"], profile)
            state["thresholds"] = {
                "warning": {"min": profile["warning"][0], "max": profile["warning"][1]},
                "critical": {"min": profile["critical"][0], "max": profile["critical"][1]},
            }
            state["sampled_at"] = now.isoformat()
        elif available and device.kind == "robot":
            command = str(state.get("command", "")).lower()
            if command in {"stop", "off"}:
                state["activity"] = "stopped"
                state["command"] = "stop"
                state.pop("active_task_id", None)
            elif device.control_mode == "manual":
                state["activity"] = state.get("activity", "stationary")
            elif state.get("active_task_id"):
                state["activity"] = state.get("activity", "working")
            else:
                state["activity"] = "patrolling" if command in {"start", "on", "reset"} else "stationary"
            position, state = _robot_step(device, devices, position, state, step_seconds)
        elif available and device.kind == "actuator":
            command = str(state.get("command", "")).lower()
            if command in {"on", "open", "start", "enable"}:
                state["output"] = "active"
            elif command in {"off", "close", "stop", "disable"}:
                state["output"] = "idle"
            else:
                state["output"] = state.get("output", "idle")
        device.state = state
        device.position = position
        device.last_updated = now
        snapshots.append({
            "id": device.id, "device_id": device.device_id, "tenant_id": device.tenant_id,
            "zone_id": device.zone_id, "name": device.name, "kind": device.kind,
            "device_type": device.device_type, "status": device.status,
            "adapter_type": device.adapter_type,
            "control_mode": device.control_mode,
            "automation_policy": device.automation_policy or {},
            "position": position, "state": state, "last_updated": now.isoformat(),
        })
    _apply_automation(devices, snapshots)
    for snapshot in snapshots:
        previous_alert = previous_alerts.get(snapshot["id"]) or None
        _apply_alert_transition(snapshot, previous_alert)
        _stage_alert_transition_audit(db, snapshot, previous_alert)
        _stage_automation_transition_audit(
            db,
            snapshot,
            previous_actuator_states.get(snapshot["id"]),
        )
    devices_by_id = {device.id: device for device in devices}
    db.add_all(
        DigitalTwinTelemetry(
            tenant_id=snapshot["tenant_id"],
            device_id=devices_by_id[snapshot["id"]].id,
            snapshot=snapshot,
            recorded_at=now,
        )
        for snapshot in snapshots
    )
    db.commit()
    return snapshots