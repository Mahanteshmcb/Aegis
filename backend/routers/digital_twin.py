"""Tenant-scoped virtual device APIs for the Day 74 simulation foundation."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend import realtime
from backend.database import SessionLocal
from backend.dependencies import get_current_user
from backend.models.digital_twin import DigitalTwinDevice
from backend.services import digital_twin

router = APIRouter(prefix="/api/v1/digital-twin", tags=["digital-twin"])


class DeviceCreate(BaseModel):
    device_id: str
    name: str
    kind: str
    device_type: str
    zone_id: int | None = None
    position: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
    state: Dict[str, Any] = {}
    control_mode: str = "automation"
    automation_policy: Dict[str, Any] = {}


class DeviceControl(BaseModel):
    command: str
    parameters: Dict[str, Any] = {}


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
        "position": device.position or {},
        "state": device.state or {},
        "simulation_enabled": device.simulation_enabled,
        "control_mode": device.control_mode,
        "automation_policy": device.automation_policy or {},
        "last_updated": device.last_updated.isoformat() if device.last_updated else None,
    }


def _tenant_id(user) -> int:
    return int(user.tenant_id if hasattr(user, "tenant_id") else user["tenant_id"])


@router.get("/devices")
def list_devices(current_user=Depends(get_current_user)) -> List[dict]:
    with SessionLocal() as db:
        rows = db.query(DigitalTwinDevice).filter(DigitalTwinDevice.tenant_id == _tenant_id(current_user)).all()
        return [_snapshot(row) for row in rows]


@router.post("/devices")
def create_device(schema: DeviceCreate, current_user=Depends(get_current_user)) -> dict:
    if schema.kind not in digital_twin.DEVICE_KINDS:
        raise HTTPException(status_code=422, detail="kind must be sensor, robot, or actuator")
    if schema.control_mode not in {"manual", "automation", "ai"}:
        raise HTTPException(status_code=422, detail="control_mode must be manual, automation, or ai")
    with SessionLocal() as db:
        tenant_id = _tenant_id(current_user)
        existing = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.tenant_id == tenant_id,
            DigitalTwinDevice.device_id == schema.device_id,
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="device_id already exists for this tenant")
        device = DigitalTwinDevice(tenant_id=tenant_id, **schema.dict())
        db.add(device)
        db.commit()
        db.refresh(device)
        return _snapshot(device)


@router.post("/devices/{device_id}/control")
def control_device(device_id: int, command: DeviceControl, current_user=Depends(get_current_user)) -> dict:
    """Apply a manual command while retaining the device's selected control mode."""
    with SessionLocal() as db:
        device = db.query(DigitalTwinDevice).filter(
            DigitalTwinDevice.id == device_id,
            DigitalTwinDevice.tenant_id == _tenant_id(current_user),
        ).first()
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        state = dict(device.state or {})
        state["command"] = command.command
        state.update(command.parameters)
        device.state = state
        device.status = "online"
        db.commit()
        db.refresh(device)
        return _snapshot(device)


@router.post("/tick")
async def advance_simulation(current_user=Depends(get_current_user)) -> dict:
    with SessionLocal() as db:
        snapshots = digital_twin.tick_once(db, tenant_id=_tenant_id(current_user))
    for snapshot in snapshots:
        await realtime.sio.emit("digital_twin:device_update", snapshot)
    return {"updated": len(snapshots), "devices": snapshots}