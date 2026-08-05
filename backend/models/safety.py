"""
Safety models: SafetyRule, SafetyEvent, EmergencyStop
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class SafetyRule(Base):
    __tablename__ = "safety_rules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(200), nullable=False)
    sensor_type = Column(String(100), nullable=False)
    metric = Column(String(100), nullable=False)  # e.g., "co2.ppm" or "temperature"
    operator = Column(String(10), nullable=False)  # 'lt' or 'gt'
    threshold = Column(Float, nullable=False)
    severity = Column(String(50), default="warning")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SafetyEvent(Base):
    __tablename__ = "safety_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("safety_rules.id"), nullable=True)
    message = Column(Text, nullable=False)
    severity = Column(String(50), default="warning")
    created_at = Column(DateTime, default=datetime.utcnow)

    rule = relationship("SafetyRule")


class EmergencyStop(Base):
    __tablename__ = "emergency_stop"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    active = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PerimeterLockdown(Base):
    __tablename__ = "perimeter_lockdown"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    active = Column(Boolean, default=False)
    reason = Column(String(255), nullable=True)
    initiated_by = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AccessControlEvent(Base):
    __tablename__ = "access_control_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    user_name = Column(String(200), nullable=True)
    method = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    location = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SecurityPatrol(Base):
    __tablename__ = "security_patrols"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    active = Column(Boolean, default=False)
    route_name = Column(String(200), nullable=True)
    assigned_robot = Column(String(100), nullable=True)
    status = Column(String(50), default="idle")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EvacuationProtocol(Base):
    __tablename__ = "evacuation_protocols"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    active = Column(Boolean, default=False)
    initiated_by = Column(String(120), nullable=True)
    incident_type = Column(String(120), nullable=True)
    affected_zones = Column(String(500), nullable=True)
    stage = Column(String(120), default="standby")
    instructions = Column(Text, nullable=True)
    reason = Column(String(255), nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
