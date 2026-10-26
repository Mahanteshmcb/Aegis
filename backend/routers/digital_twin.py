"""Tenant-scoped virtual device APIs for the Day 74 simulation foundation."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import realtime
from backend.database import SessionLocal, Zone
from backend.dependencies import get_current_user, has_permission
from backend.models.digital_twin import DigitalTwinDevice
from backend.services import digital_twin
from backend.device_adapters import (
    AdapterCommandError,
    AdapterUnavailableError,
    TelemetryValidationError,
    SUPPORTED_ADAPTER_TYPES,
    adapter_registry,
    device_context,
    dispatch_command,
)

router = APIRouter(prefix="/api/v1/digital-twin", tags=["digital-twin"])
CONTROL_COMMANDS = {"on", "off", "start", "stop", "open", "close", "enable", "disable", "reset"}


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    kind: str
    device_type: str
    adapter_type: str = "simulation"
    zone_id: int | None = None
    position: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
    state: Dict[str, Any] = {}
    control_mode: str = "automation"
    automation_policy: Dict[str, Any] = {}


class DeviceControl(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}


class DeviceUpdate(BaseModel):
    name: str | None = None
    kind: str | None = None
    device_type: str | None = None
    zone_id: int | None = None
    status: str | None = None
    adapter_type: str | None = None
    position: Dict[str, float] | None = None
    state: Dict[str, Any] | None = None
    simulation_enabled: bool | None = None
    control_mode: str | None = None
    automation_policy: Dict[str, Any] | None = None


def _snapshot(device: DigitalTwinDevice) -> dict:
    return {
        "id": device.id,
        "device_id": device.device_id,
        "tenant_id": device.tenant_id,
        "zone_id": device.zone_id,
        "name": device.name,
        "kind": device.kind,
        "device_type": device.device_type,
        "status": device.status,
        "adapter_type": device.adapter_type,
        "position": device.position or {},
        "state": device.state or {},
        "simulation_enabled": device.simulation_enabled,
        "control_mode": device.control_mode,
        "automation_policy": device.automation_policy or {},
        "last_updated": device.last_updated.isoformat() if device.last_updated else None,
    }


def _tenant_id(user) -> int:
    return int(user.tenant_id if hasattr(user, "tenant_id") else user["tenant_id"])


def _ensure_permission(user, permission: str) -> None:
    if not has_permission(user, permission):
        raise HTTPException(status_code=403, detail=f"Device operation requires {permission}")


def _validate_zone_ownership(db, tenant_id: int, zone_id: int | None) -> None:
    if zone_id is None:
        return
    zone = db.query(Zone.id).filter(
        Zone.id == zone_id,
        Zone.tenant_id == tenant_id,
    ).first()
    if zone is None:
        raise HTTPException(status_code=404, detail="Zone not found")


def _record_device_audit(db, current_user, event_type: str, device: DigitalTwinDevice, details: Dict[str, Any] | None = None) -> None:
    metadata = {
        **(details or {}),
        "action": event_type,
        "actor_user_id": current_user.get("id") if isinstance(current_user, dict) else getattr(current_user, "id", None),
        "actor_email": current_user.get("email") if isinstance(current_user, dict) else getattr(current_user, "email", None),
        "entity_type": device.kind,
        "entity_id": device.device_id,
        "device_name": device.name,
        "device_type": device.device_type,
        "zone_id": device.zone_id,
        "outcome": "success",
    }
    from backend.audit_utils import record_audit_event
    from backend.blockchain_connector import get_blockchain_connector
    record_audit_event(db, get_blockchain_connector(), _tenant_id(current_user), event_type, metadata)


@router.get("/devices")
def list_devices(current_user=Depends(get_current_user)) -> List[dict]:
    with SessionLocal() as db:
        rows = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.tenant_id == _tenant_id(current_user)).all()
        return [_snapshot(row) for row in rows]


@router.get("/devices/{device_id}")
def get_device(device_id: int, current_user=Depends(get_current_user)) -> dict:
    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        _record_device_audit(db, current_user, "device_viewed", device, {"view": "detail"})
        return _snapshot(device)


@router.get("/health")
def twin_health(current_user=Depends(get_current_user)) -> dict:
    with SessionLocal() as db:
        devices = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.tenant_id == _tenant_id(current_user)).all()
        online = [device for device in devices if device.status == "online"]
        sensors = [device for device in devices if device.kind == "sensor"]
        actuators = [device for device in devices if device.kind == "actuator"]
        alerts = [
            device for device in sensors
            if (device.state or {}).get("reading_status") in {"warning", "critical"}
        ]
        health = 100 if not devices else round((len(online) / len(devices)) * 100)
        recommendations = digital_twin.build_predictive_recommendations(devices)
        optimization = digital_twin.build_optimization_recommendations(devices)
        adaptation = digital_twin.build_adaptation_recommendations(devices)
        recommendation_summary = digital_twin.build_recommendation_summary(recommendations, optimization, adaptation)
        alert_summary = digital_twin.build_alert_summary(devices)
        stability = digital_twin.build_stability_summary(devices)
        workflow = digital_twin.build_workflow_summary(
            recommendations,
            optimization,
            adaptation,
            health_score=health,
            alert_summary=alert_summary,
            stability=stability,
        )
        api_status = digital_twin.build_api_status(health, devices, alert_summary)
        session = digital_twin.build_session_summary(tenant_id=_tenant_id(current_user), active=True)
        interaction_summary = digital_twin.build_interaction_summary(devices)
        return {
            "status": "healthy" if health >= 80 else "degraded" if health >= 50 else "critical",
            "health_score": health,
            "devices": len(devices),
            "online": len(online),
            "sensors": len(sensors),
            "actuators": len(actuators),
            "active_actuators": sum(1 for device in actuators if (device.state or {}).get("output") == "active"),
            "alerts": len(alerts),
            "recommendations": recommendations,
            "optimization": optimization,
            "adaptation": adaptation,
            "recommendation_summary": recommendation_summary,
            "alert_summary": alert_summary,
            "stability": stability,
            "workflow": workflow,
            "api_status": api_status,
            "session": session,
            "interaction_summary": interaction_summary,
        }


@router.post("/devices")
def create_device(schema: DeviceCreate, current_user=Depends(get_current_user)) -> dict:
    _ensure_permission(current_user, "devices.manage")
    if schema.kind not in digital_twin.DEVICE_KINDS:
        raise HTTPException(status_code=422, detail="kind must be sensor, robot, or actuator")
    if schema.control_mode not in {"manual", "automation", "ai"}:
        raise HTTPException(status_code=422, detail="control_mode must be manual, automation, or ai")
    if schema.adapter_type not in SUPPORTED_ADAPTER_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"adapter_type must be one of {sorted(SUPPORTED_ADAPTER_TYPES)}",
        )
    if schema.adapter_type == "serial" and (
        schema.kind != "actuator" or schema.device_id != "mega-onboard-led-01"
    ):
        raise HTTPException(
            status_code=422,
            detail="The configured serial pilot supports only the mega-onboard-led-01 actuator",
        )
    with SessionLocal() as db:
        tenant_id = _tenant_id(current_user)
        _validate_zone_ownership(db, tenant_id, schema.zone_id)
        existing = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.tenant_id == tenant_id,
            DigitalTwinDevice.device_id == schema.device_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="device_id already exists for this tenant")
        device_data = schema.dict()
        device_data["simulation_enabled"] = schema.adapter_type == "simulation"
        device = DigitalTwinDevice(tenant_id=tenant_id, **device_data)
        db.add(device)
        _record_device_audit(db, current_user, "device_created", device, {"state": device.state or {}, "position": device.position or {}})
        db.refresh(device)
        return _snapshot(device)


@router.put("/devices/{device_id}")
def update_device(device_id: int, schema: DeviceUpdate, current_user=Depends(get_current_user)) -> dict:
    _ensure_permission(current_user, "devices.manage")
    if schema.kind is not None and schema.kind not in digital_twin.DEVICE_KINDS:
        raise HTTPException(status_code=422, detail="kind must be sensor, robot, or actuator")
    if schema.control_mode is not None and schema.control_mode not in {"manual", "automation", "ai"}:
        raise HTTPException(status_code=422, detail="control_mode must be manual, automation, or ai")
    if schema.adapter_type is not None and schema.adapter_type not in SUPPORTED_ADAPTER_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"adapter_type must be one of {sorted(SUPPORTED_ADAPTER_TYPES)}",
        )

    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        changes = schema.dict(exclude_unset=True)
        effective_adapter = changes.get("adapter_type", device.adapter_type)
        if effective_adapter == "serial" and (
            changes.get("kind", device.kind) != "actuator"
            or device.device_id != "mega-onboard-led-01"
        ):
            raise HTTPException(
                status_code=422,
                detail="The configured serial pilot supports only the mega-onboard-led-01 actuator",
            )
        if "adapter_type" in changes:
            expected_simulation = changes["adapter_type"] == "simulation"
            if "simulation_enabled" in changes and changes["simulation_enabled"] != expected_simulation:
                raise HTTPException(
                    status_code=422,
                    detail="simulation_enabled must be false for hardware adapters and true for simulation",
                )
            changes["simulation_enabled"] = expected_simulation
        elif changes.get("simulation_enabled") and device.adapter_type != "simulation":
            raise HTTPException(
                status_code=422,
                detail="Hardware-backed devices cannot enable software simulation",
            )
        if "zone_id" in changes:
            _validate_zone_ownership(db, _tenant_id(current_user), changes["zone_id"])
        for field, value in changes.items():
            if field == "zone_id" or value is not None:
                setattr(device, field, value)
        _record_device_audit(db, current_user, "device_updated", device, {"changed_fields": list(changes.keys()), "changes": changes})
        db.refresh(device)
        return _snapshot(device)


@router.delete("/devices/{device_id}")
def delete_device(device_id: int, current_user=Depends(get_current_user)) -> dict:
    _ensure_permission(current_user, "devices.manage")
    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        deleted_id = device.device_id
        db.delete(device)
        _record_device_audit(db, current_user, "device_deleted", device)
        return {"deleted": True, "device_id": deleted_id}


@router.post("/devices/{device_id}/control")
def control_device(device_id: int, command: DeviceControl, current_user=Depends(get_current_user)) -> dict:
    """Apply a manual command while retaining the device's selected control mode."""
    _ensure_permission(current_user, "devices.control")
    if command.command.lower() not in CONTROL_COMMANDS:
        raise HTTPException(status_code=422, detail="Unsupported device command")
    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        if device.status.lower() != "online":
            raise HTTPException(status_code=409, detail="Cannot control an offline device")

        try:
            _, acknowledgement = dispatch_command(device, command.command.lower(), command.parameters)
        except AdapterUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except AdapterCommandError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        state = dict(device.state or {})
        if device.adapter_type == "simulation":
            state["command"] = command.command.lower()
            state.update(command.parameters)
        else:
            state["requested_command"] = command.command.lower()
            state["requested_parameters"] = command.parameters
            if acknowledgement.confirmed and acknowledgement.state in {"ON", "OFF"}:
                state["output"] = "active" if acknowledgement.state == "ON" else "idle"
                state["confirmed_at"] = acknowledgement.acknowledged_at
        state["last_command_delivery"] = acknowledgement.to_payload()
        device.state = state
        if device.adapter_type == "simulation":
            device.status = "online"
        _record_device_audit(db, current_user, "device_commanded", device, {
            "command": command.command,
            "parameters": command.parameters,
            "delivery": acknowledgement.to_payload(),
            "response": _snapshot(device),
        })
        db.refresh(device)
        return _snapshot(device)


@router.post("/devices/{device_id}/telemetry")
async def ingest_device_telemetry(
    device_id: int,
    payload: Dict[str, Any],
    current_user=Depends(get_current_user),
) -> dict:
    """Validate transport telemetry, then persist it through the canonical twin history."""
    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if device is None:
            raise HTTPException(status_code=404, detail="Device not found")
        try:
            adapter = adapter_registry.get(device.adapter_type)
            telemetry = adapter.normalize_telemetry(device_context(device), payload)
        except AdapterUnavailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except TelemetryValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        if device.kind != "sensor":
            raise HTTPException(status_code=422, detail="Telemetry can only be ingested for sensor devices")
        try:
            snapshots = digital_twin.ingest_sensor_sample(
                db, device, telemetry.value, telemetry.unit, telemetry.sampled_at
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        for snapshot in snapshots:
            await realtime.emit_tenant_event(
                "digital_twin:device_update", snapshot, telemetry.tenant_id
            )
            if snapshot.get("alert"):
                await realtime.emit_tenant_event(
                    "digital_twin:alert", snapshot["alert"], telemetry.tenant_id
                )
            if snapshot.get("alert_cleared"):
                await realtime.emit_tenant_event(
                    "digital_twin:alert_cleared", snapshot["alert_cleared"], telemetry.tenant_id
                )
        return {"device": _snapshot(device), "telemetry": telemetry.to_payload()}


@router.post("/tick")
async def advance_simulation(current_user=Depends(get_current_user)) -> dict:
    _ensure_permission(current_user, "devices.control")
    with SessionLocal() as db:
        snapshots = digital_twin.tick_once(db, tenant_id=_tenant_id(current_user))
    for snapshot in snapshots:
        tenant_id = snapshot.get("tenant_id", _tenant_id(current_user))
        await realtime.emit_tenant_event("digital_twin:device_update", snapshot, tenant_id)
        if snapshot.get("alert"):
            await realtime.emit_tenant_event("digital_twin:alert", snapshot["alert"], tenant_id)
        if snapshot.get("alert_cleared"):
            await realtime.emit_tenant_event("digital_twin:alert_cleared", snapshot["alert_cleared"], tenant_id)
    return {"updated": len(snapshots), "devices": snapshots}