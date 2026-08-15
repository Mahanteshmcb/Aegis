"""Scene entity models for Day 73 digital twin scene objects."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy import JSON as SAJSON

from backend.database import Base


class SceneEntity(Base):
    __tablename__ = "scene_entities"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=True, index=True)
    name = Column(String(128), nullable=False)
    type = Column(String(64), nullable=True)
    x = Column(Float, default=0.0)
    y = Column(Float, default=0.0)
    z = Column(Float, default=0.0)
    rotation = Column(Float, default=0.0)
    state = Column(SAJSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
