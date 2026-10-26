from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db
from backend.routers.robotics import get_robotics_connector
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["Robotics Compatibility"])

class TaskCreate(BaseModel):
    name: str
    robot_id: Optional[str] = None
    assigned_to: Optional[int] = None
    priority: str = "medium"
    status: str = "pending"
    due_date: Optional[str] = None
    description: Optional[str] = ""
    operation_type: Optional[str] = None
    zone_id: Optional[str] = None
    task_detail: Optional[Dict[str, Any]] = {}

class TaskResponse(BaseModel):
    id: str
    name: str
    robot_id: Optional[str]
    priority: str
    status: str
    due_date: Optional[str]
    description: Optional[str]
    created_at: str
    zone_id: Optional[str]

@router.post("/tasks", response_model=TaskResponse)
async def create_task(payload: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    task_id = f"task-{uuid4().hex[:10]}"
    task_detail = dict(payload.task_detail or {})
    task_detail["name"] = payload.name
    task_detail["description"] = payload.description or ""
    try:
        db_task = crud.create_scheduled_task(
            db,
            schemas.ScheduledTaskCreate(
                task_id=task_id,
                operation_type=payload.operation_type or "generic",
                requested_robot_id=payload.robot_id,
                zone_id=payload.zone_id,
                priority=5 if payload.priority == "medium" else (1 if payload.priority == "high" else 3),
                task_detail=task_detail,
                metadata={},
                timeout_seconds=60,
                status=payload.status,
            ),
            tenant_id=tenant_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=409, detail=str(err))
    _record_robotics_compat_action(
        db, current_user, "robot_task_created", db_task.task_id,
        {
            "operation_type": db_task.operation_type,
            "requested_robot_id": db_task.requested_robot_id,
            "zone_id": db_task.zone_id,
            "priority": db_task.priority,
            "status": db_task.status,
            "name": task_detail["name"],
        },
    )
    return _task_to_response(db_task)

@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: str, payload: TaskCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    task = crud.get_scheduled_task_by_task_id(db, tenant_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task_detail = dict(task.task_detail or {})
    task_detail["name"] = payload.name
    task_detail["description"] = payload.description or ""
    task.task_detail = task_detail
    if payload.zone_id is not None:
        task.zone_id = payload.zone_id
    if payload.robot_id is not None:
        task.requested_robot_id = payload.robot_id
    task.status = payload.status
    task.updated_at = datetime.utcnow()
    db.add(task)
    _record_robotics_compat_action(
        db, current_user, "robot_task_updated", task.task_id,
        {
            "operation_type": task.operation_type,
            "requested_robot_id": task.requested_robot_id,
            "zone_id": task.zone_id,
            "priority": task.priority,
            "status": task.status,
            "name": task_detail["name"],
        },
    )
    db.refresh(task)
    return _task_to_response(task)

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    deleted = crud.delete_scheduled_task(db, tenant_id, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    _record_robotics_compat_action(
        db, current_user, "robot_task_deleted", task_id, {},
    )
    return {"detail": "Task deleted"}
@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    tasks = crud.list_scheduled_tasks(db, tenant_id)
    return [_task_to_response(t) for t in tasks]

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    tenant_id = current_user.get("tenant_id") if isinstance(current_user, dict) else getattr(current_user, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Tenant missing from current user")
    task = crud.get_scheduled_task_by_task_id(db, tenant_id, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return _task_to_response(task)
class TaskCreate(BaseModel):
    name: str
    robot_id: Optional[str] = None
    assigned_to: Optional[int] = None
    priority: str = "medium"
    status: str = "pending"
    due_date: Optional[str] = None
    description: Optional[str] = ""
    operation_type: Optional[str] = None
    zone_id: Optional[str] = None
    task_detail: Optional[Dict[str, Any]] = {}

class TaskResponse(BaseModel):
    id: str
    name: str
    robot_id: Optional[str]
    priority: str
    status: str
    due_date: Optional[str]
    description: Optional[str]
    created_at: str
    zone_id: Optional[str]

def _task_to_response(task: models.ScheduledRoboticTask) -> TaskResponse:
    return TaskResponse(
        id=task.task_id,
        name=(task.task_detail or {}).get("name", task.task_id),
        robot_id=task.assigned_robot_id or task.requested_robot_id,
        priority=str(task.priority),
        status=task.status,
        due_date=task.due_date.isoformat() if getattr(task, "due_date", None) else None,
        description=(task.task_detail or {}).get("description", ""),
        created_at=task.created_at.isoformat() if task.created_at else "",
        zone_id=task.zone_id,
    )
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.dependencies import get_current_user, get_db
from backend import crud, models_db as models
from backend import schemas


def _record_robotics_compat_action(db: Session, actor: dict, event_type: str, task_id: str, details: dict):
    from backend.audit_utils import record_actor_audit_event
    from backend.blockchain_connector import get_blockchain_connector

    return record_actor_audit_event(
        db, actor["tenant_id"], actor, event_type, "scheduled_robotic_task", task_id,
        details, blockchain=get_blockchain_connector(),
    )


async def list_robots(current_user=Depends(get_current_user)):
    connector = get_robotics_connector()
    return connector.list_active_robots()