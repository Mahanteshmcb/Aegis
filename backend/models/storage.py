from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class StorageFacility(Base):
    __tablename__ = "storage_facilities"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    name = Column(String(120), nullable=False)
    location = Column(String(200), nullable=True)
    type = Column(String(50), nullable=True)  # e.g., cold, dry, chemical
    capacity = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    inventory_items = relationship("InventoryItem", back_populates="facility")

class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    facility_id = Column(Integer, ForeignKey("storage_facilities.id"), nullable=False)
    name = Column(String(120), nullable=False)
    description = Column(String(300), nullable=True)
    quantity = Column(Float, nullable=False, default=0)
    unit = Column(String(30), nullable=True)
    lot_number = Column(String(80), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    facility = relationship("StorageFacility", back_populates="inventory_items")