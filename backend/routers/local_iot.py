"""Local-first operational runtime endpoints for tenant-local device and command flow."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_current_user
from backend.services.local_iot_runtime import runtime

router = APIRouter(prefix="/api/v1/local-iot", tags=["local-iot"])


class LocalDeviceCreate(BaseModel):
    device_id: str
    name: str
    kind: str
    device_type: str
    zone_id: Optional[int] = None
    status: str = "online"
    position: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
    metadata: Dict[str, Any] = {}


class LocalTelemetryIngest(BaseModel):
    device_id: str
    value: float
    unit: str = "raw"
    sensor_type: Optional[str] = None
    zone_id: Optional[int] = None


class LocalCommandPayload(BaseModel):
    device_id: str
    command: str
    parameters: Dict[str, Any] = {}
    zone_id: Optional[int] = None


@router.get("/devices")
def list_devices(current_user=Depends(get_current_user)) -> List[Dict[str, Any]]:
    tenant_id = int(current_user["tenant_id"])
    return runtime.list_devices(tenant_id=tenant_id)


@router.post("/devices")
def register_device(payload: LocalDeviceCreate, current_user=Depends(get_current_user)) -> Dict[str, Any]:
    tenant_id = int(current_user["tenant_id"])
    device = runtime.register_device(
        tenant_id=tenant_id,
        zone_id=payload.zone_id,
        device_id=payload.device_id,
        name=payload.name,
        kind=payload.kind,
        device_type=payload.device_type,
        status=payload.status,
        metadata={**payload.metadata, "position": payload.position},
    )
    return {"status": "ok", "device": device}


@router.get("/zones/{zone_id}/devices")
def list_zone_devices(zone_id: int, current_user=Depends(get_current_user)) -> List[Dict[str, Any]]:
    tenant_id = int(current_user["tenant_id"])
    return runtime.list_zone_devices(zone_id, tenant_id=tenant_id)


@router.post("/telemetry")
def ingest_telemetry(payload: LocalTelemetryIngest, current_user=Depends(get_current_user)) -> Dict[str, Any]:
    tenant_id = int(current_user["tenant_id"])
    device = runtime.get_device(payload.device_id)
    if not device or device.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Device not found for this tenant")
    device = runtime.record_telemetry(
        device_id=payload.device_id,
        value=payload.value,
        unit=payload.unit,
        sensor_type=payload.sensor_type,
        zone_id=payload.zone_id,
    )
    return {"status": "ok", "device": device}


@router.post("/commands")
def queue_command(payload: LocalCommandPayload, current_user=Depends(get_current_user)) -> Dict[str, Any]:
    tenant_id = int(current_user["tenant_id"])
    device = runtime.get_device(payload.device_id)
    if not device or device.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Device not found for this tenant")
    record = runtime.queue_command(
        device_id=payload.device_id,
        command=payload.command,
        parameters=payload.parameters,
        zone_id=payload.zone_id,
        created_by=current_user.get("email", "operator"),
    )
    return {"status": "queued", "command": record}


@router.post("/commands/execute")
def execute_command(payload: LocalCommandPayload, current_user=Depends(get_current_user)) -> Dict[str, Any]:
    tenant_id = int(current_user["tenant_id"])
    device = runtime.get_device(payload.device_id)
    if not device or device.get("tenant_id") != tenant_id:
        raise HTTPException(status_code=404, detail="Device not found for this tenant")
    updated = runtime.execute_command(
        device_id=payload.device_id,
        command=payload.command,
        parameters=payload.parameters,
        actor=current_user.get("email", "operator"),
    )
    return {"status": "executed", "device": updated}


@router.get("/twin")
def twin_snapshot(current_user=Depends(get_current_user)) -> Dict[str, Any]:
    tenant_id = int(current_user["tenant_id"])
    snapshot = runtime.get_twin_snapshot()
    snapshot["devices"] = [item for item in snapshot["devices"] if item.get("tenant_id") == tenant_id]
    snapshot["zones"] = [{**item, "device_ids": [device_id for device_id in item.get("device_ids", []) if runtime.get_device(device_id) and runtime.get_device(device_id).get("tenant_id") == tenant_id]} for item in snapshot["zones"]]
    snapshot["command_queue"] = [item for item in snapshot["command_queue"] if runtime.get_device(item["device_id"]) and runtime.get_device(item["device_id"]).get("tenant_id") == tenant_id]
    snapshot["events"] = [item for item in snapshot["events"] if not item.get("device_id") or (runtime.get_device(item["device_id"]) and runtime.get_device(item["device_id"]).get("tenant_id") == tenant_id)]
    return snapshot
