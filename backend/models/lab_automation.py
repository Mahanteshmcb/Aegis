"""
Lab Automation models — devices, jobs, schedules, execution logs
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class AutomationDevice(Base):
    __tablename__ = "automation_devices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    name = Column(String(120), nullable=False)
    device_type = Column(String(80), nullable=False)  # e.g., pipettor, incubator, plate_reader
    capabilities = Column(JSON, nullable=True)
    # safety interlock: when True, remote commands are blocked until cleared
    interlocked = Column(Boolean, default=False)
    # required minimum role to operate this device (viewer/operator/admin)
    required_role = Column(String(30), default="operator")
    status = Column(String(30), default="offline")
    last_seen = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # relationships
    jobs = relationship("AutomationJob", back_populates="device")


class AutomationJob(Base):
    __tablename__ = "automation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("automation_devices.id"), nullable=True)
    name = Column(String(200), nullable=False)
    command = Column(Text, nullable=False)  # a short instruction or command identifier
    parameters = Column(JSON, nullable=True)
    scheduled_at = Column(DateTime, nullable=True)
    cron = Column(String(120), nullable=True)  # optional cron expression for recurring jobs
    recurring = Column(Boolean, default=False)
    status = Column(String(30), default="pending")  # pending, running, completed, failed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    device = relationship("AutomationDevice", back_populates="jobs")
    executions = relationship("AutomationExecutionLog", back_populates="job")


class AutomationExecutionLog(Base):
    __tablename__ = "automation_execution_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("automation_jobs.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("automation_devices.id"), nullable=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    status = Column(String(30), nullable=False)  # started, success, failure
    output = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    job = relationship("AutomationJob", back_populates="executions")
