"""
Aegis Backend - Audit Logs Router
Admin-only endpoints for viewing and filtering audit logs.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_admin
from backend import crud, schemas

router = APIRouter(prefix="/api/v1", tags=["audit"])

@router.get("/audit/logs", response_model=list[schemas.AuditLog])
async def list_audit_logs(
    sensor_id: int = Query(None, description="Filter by sensor ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    List audit logs (admin only). Optionally filter by sensor_id.
    """
    if sensor_id is not None:
        logs = crud.list_audit_logs(db, sensor_id=sensor_id, skip=skip, limit=limit)
    else:
        # List all logs for the admin's tenant by joining sensors
        from backend.models_db import Sensor, AuditLog
        logs = (
            db.query(AuditLog)
            .join(Sensor, AuditLog.sensor_id == Sensor.id)
            .filter(Sensor.tenant_id == current_admin["tenant_id"])
            .offset(skip)
            .limit(limit)
            .all()
        )
    return logs
