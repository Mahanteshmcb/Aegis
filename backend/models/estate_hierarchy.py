"""Tenant-scoped estate hierarchy for customer-specific digital twins."""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String

from backend.database import Base


class Estate(Base):
    __tablename__ = "estates"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    layout = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EstateNode(Base):
    __tablename__ = "estate_nodes"

    id = Column(Integer, primary_key=True, index=True)
    estate_id = Column(Integer, ForeignKey("estates.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("estate_nodes.id"), nullable=True, index=True)
    node_type = Column(String(32), nullable=False)  # zone, building, room, section
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    position = Column(JSON, default=lambda: {"x": 0.0, "y": 0.0, "z": 0.0})
    dimensions = Column(JSON, default=lambda: {"x": 10.0, "y": 3.0, "z": 10.0})
    node_metadata = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)