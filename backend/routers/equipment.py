"""
Equipment control endpoints with safety interlocks and RBAC.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.dependencies import get_db, get_current_user
from backend.models.lab_automation import AutomationExecutionLog
from backend import models_db
from backend.services.automation_scheduler import check_safety_for_tenant
from backend.services import broadcast

router = APIRouter(prefix="/api/v1/equipment", tags=["equipment"])


class CommandRequest(BaseModel):
    command: str
    parameters: dict = {}


@router.post("/{device_id}/command")
def send_command(device_id: int, payload: CommandRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    # RBAC and device-specific checks
    role = current_user.get("role", "viewer")

    device = db.query(models_db.AutomationDevice).filter(models_db.AutomationDevice.id == device_id, models_db.AutomationDevice.tenant_id == current_user["tenant_id"]).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # check device interlock
    if getattr(device, 'interlocked', False):
        raise HTTPException(status_code=423, detail="Device is interlocked and cannot accept commands")

    # check required role for this device
    required = (device.required_role or 'operator')
    allowed_roles = {
        'viewer': ['viewer', 'operator', 'admin'],
        'operator': ['operator', 'admin'],
        'admin': ['admin']
    }
    if role not in allowed_roles.get(required, ['operator', 'admin']):
        raise HTTPException(status_code=403, detail="Insufficient role to command this device")

    # Safety pre-check (tenant-wide)
    blocked, reason, rule_id = check_safety_for_tenant(db, current_user["tenant_id"])  # reuses scheduler helper
    if blocked:
        raise HTTPException(status_code=423, detail=f"Command blocked by safety: {reason}")

    # For demo: record a simple execution log and mark device last seen
    try:
        device.last_seen = None
        db.add(device)
        log = AutomationExecutionLog(
            job_id=None,
            device_id=device_id,
            tenant_id=current_user["tenant_id"],
            status="started",
            output=f"Command: {payload.command} params={payload.parameters}",
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        # Simulate immediate success
        log.status = "success"
        db.add(log)
        db.commit()

        # publish event for UI
        try:
            import asyncio
            asyncio.create_task(broadcast.publish({
                'type': 'equipment_command',
                'tenant_id': current_user["tenant_id"],
                'device_id': device_id,
                'command': payload.command,
                'parameters': payload.parameters,
                'status': 'success',
            }))
        except Exception:
            pass

        return {"status": "ok", "log_id": log.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
