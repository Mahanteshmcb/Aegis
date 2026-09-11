"""Persisted virtual devices used by the Day 74 digital-twin simulator."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String

from backend.database import Base


class DigitalTwinDevice(Base):
    __tablename__ = "digital_twin_devices"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    device_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    kind = Column(String(32), nullable=False)
    device_type = Column(String(100), nullable=False)
    status = Column(String(32), nullable=False, default="online")
    position = Column(JSON, default=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    state = Column(JSON, default=dict)
    simulation_enabled = Column(Boolean, nullable=False, default=True)
    control_mode = Column(String(24), nullable=False, default="automation")
    automation_policy = Column(JSON, default=dict)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)