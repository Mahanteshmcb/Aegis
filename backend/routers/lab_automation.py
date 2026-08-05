"""
Lab Automation API Routes
Provides basic device and job management endpoints for lab automation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from backend.dependencies import get_db, get_current_user
from backend.models.lab_automation import AutomationDevice, AutomationJob, AutomationExecutionLog
from backend.database import SessionLocal
import asyncio
from datetime import datetime

router = APIRouter(prefix="/api/v1/lab", tags=["lab_automation"])


class DeviceCreate(BaseModel):
    name: str
    device_type: str
    zone_id: Optional[int] = None
    capabilities: Optional[dict] = None


class DeviceResponse(BaseModel):
    id: int
    name: str
    device_type: str
    status: str


@router.post("/devices", response_model=DeviceResponse)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    device = AutomationDevice(
        tenant_id=current_user["tenant_id"],
        zone_id=payload.zone_id,
        name=payload.name,
        device_type=payload.device_type,
        capabilities=payload.capabilities or {},
        status="online",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/devices", response_model=List[DeviceResponse])
def list_devices(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    devices = db.query(AutomationDevice).filter(AutomationDevice.tenant_id == current_user["tenant_id"]).all()
    return devices


class JobCreate(BaseModel):
    name: str
    device_id: Optional[int] = None
    command: str
    parameters: Optional[dict] = None
    scheduled_at: Optional[datetime] = None
    recurring: Optional[bool] = False
    cron: Optional[str] = None


class JobResponse(BaseModel):
    id: int
    name: str
    status: str
    scheduled_at: Optional[datetime]


@router.post("/jobs", response_model=JobResponse)
def create_job(payload: JobCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = AutomationJob(
        tenant_id=current_user["tenant_id"],
        device_id=payload.device_id,
        name=payload.name,
        command=payload.command,
        parameters=payload.parameters or {},
        scheduled_at=payload.scheduled_at,
        recurring=bool(payload.recurring),
        cron=payload.cron,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    jobs = db.query(AutomationJob).filter(AutomationJob.tenant_id == current_user["tenant_id"]).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id, AutomationJob.tenant_id == current_user["tenant_id"]).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id, AutomationJob.tenant_id == current_user["tenant_id"]).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "cancelled"
    db.commit()
    return {"status": "cancelled", "job_id": job_id}


@router.post("/jobs/{job_id}/run")
def run_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Trigger a job run immediately (synchronous request that schedules execution)."""
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id, AutomationJob.tenant_id == current_user["tenant_id"]).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Update scheduled_at to now and let background scheduler pick it up, or execute inline for quick feedback
    job.scheduled_at = datetime.utcnow()
    job.status = "pending"
    db.add(job)
    db.commit()
    return {"status": "scheduled", "job_id": job_id}


class JobUpdate(BaseModel):
    name: Optional[str] = None
    device_id: Optional[int] = None
    command: Optional[str] = None
    parameters: Optional[dict] = None
    scheduled_at: Optional[datetime] = None
    recurring: Optional[bool] = None
    cron: Optional[str] = None


@router.patch("/jobs/{job_id}", response_model=JobResponse)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id, AutomationJob.tenant_id == current_user["tenant_id"]).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if payload.name is not None:
        job.name = payload.name
    if payload.device_id is not None:
        job.device_id = payload.device_id
    if payload.command is not None:
        job.command = payload.command
    if payload.parameters is not None:
        job.parameters = payload.parameters
    if payload.scheduled_at is not None:
        job.scheduled_at = payload.scheduled_at
    if payload.recurring is not None:
        job.recurring = payload.recurring
    if payload.cron is not None:
        job.cron = payload.cron
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@router.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    job = db.query(AutomationJob).filter(AutomationJob.id == job_id, AutomationJob.tenant_id == current_user["tenant_id"]).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"status": "deleted", "job_id": job_id}


@router.get("/jobs/{job_id}/logs")
def job_logs(job_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    logs = db.query(AutomationExecutionLog).filter(AutomationExecutionLog.job_id == job_id, AutomationExecutionLog.tenant_id == current_user["tenant_id"]).order_by(AutomationExecutionLog.started_at.desc()).all()
    return [
        {
            "id": l.id,
            "status": l.status,
            "output": l.output,
            "started_at": l.started_at,
            "finished_at": l.finished_at,
        }
        for l in logs
    ]
