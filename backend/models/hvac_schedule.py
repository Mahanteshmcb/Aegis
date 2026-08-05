"""
HVAC scheduling model for zone setpoint automation.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class HVACSchedule(Base):
    __tablename__ = "hvac_schedules"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(200), nullable=False)
    setpoint = Column(Float, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)  # next run
    recurring = Column(Boolean, default=False)
    interval_days = Column(Integer, nullable=True)  # simple recurrence support
    enabled = Column(Boolean, default=True)
    cron = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # relationships
    zone = relationship("Zone")
