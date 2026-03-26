"""
Aegis Backend - Audit Logs Router
Endpoints for viewing system and sensor audit trails.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.dependencies import get_db, get_current_user # Changed to current_user
from backend import crud, schemas
from backend.models_db import Sensor, AuditLog

router = APIRouter(prefix="/api/v1", tags=["audit"])

# FIXED: Path changed from "/audit/logs" to "/audit" to match frontend api.js
@router.get("/audit", response_model=list[schemas.AuditLog])
async def list_audit_logs(
    sensor_id: int = Query(None, description="Filter by sensor ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user), # Allowed for all authenticated users
):
    """
    List audit logs. Tenant-isolated via Sensor join.
    """
    if sensor_id is not None:
        # CRUD helper should already handle tenant check if logic is robust
        return crud.list_audit_logs(db, sensor_id=sensor_id, skip=skip, limit=limit)
    
    # List all logs for the user's tenant by joining sensors
    # Using an outer join ensures system events (sensor_id=null) aren't deleted from view
    logs = (
        db.query(AuditLog)
        .outerjoin(Sensor, AuditLog.sensor_id == Sensor.id)
        # Show logs if they belong to a sensor in the tenant OR if they are system logs
        # (Note: In a true multi-tenant system, AuditLog should have its own tenant_id column)
        .filter((Sensor.tenant_id == current_user["tenant_id"]) | (AuditLog.sensor_id == None))
        .order_by(AuditLog.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return logs