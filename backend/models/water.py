"""
Water management models: collection, purification, irrigation, quality monitoring, and recycling.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class WaterCollectionSystem(Base):
    __tablename__ = "water_collection_systems"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    system_name = Column(String(200), nullable=False)
    collection_type = Column(String(100), nullable=False)  # e.g., "rainfall", "condensation", "greywater"
    capacity_liters = Column(Float, nullable=False)
    current_volume_liters = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    location = Column(String(200), nullable=True)
    last_emptied = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WaterPurificationUnit(Base):
    __tablename__ = "water_purification_units"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    unit_name = Column(String(200), nullable=False)
    purification_type = Column(String(100), nullable=False)  # e.g., "reverse_osmosis", "uv", "carbon_filter", "multi_stage"
    status = Column(String(50), default="ready")  # "ready", "active", "maintenance", "offline"
    flow_rate_lpm = Column(Float, nullable=True)  # liters per minute
    efficiency_percent = Column(Float, default=95.0)
    input_volume_liters = Column(Float, default=0.0)
    output_volume_liters = Column(Float, default=0.0)
    last_maintenance = Column(DateTime, nullable=True)
    maintenance_interval_days = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IrrigationSystem(Base):
    __tablename__ = "irrigation_systems"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    system_name = Column(String(200), nullable=False)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    irrigation_type = Column(String(100), nullable=False)  # e.g., "drip", "sprinkler", "hydroponic", "micro"
    status = Column(String(50), default="idle")  # "idle", "watering", "scheduled"
    scheduled_frequency_minutes = Column(Integer, nullable=True)
    last_watering = Column(DateTime, nullable=True)
    next_scheduled_watering = Column(DateTime, nullable=True)
    water_per_cycle_liters = Column(Float, nullable=True)
    optimization_enabled = Column(Boolean, default=True)
    soil_moisture_target_percent = Column(Float, default=60.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WaterQualityReading(Base):
    __tablename__ = "water_quality_readings"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    reading_location = Column(String(200), nullable=False)  # "collection", "purified", "irrigation_input", "irrigation_output"
    ph_level = Column(Float, nullable=True)
    turbidity_ntu = Column(Float, nullable=True)  # Nephelometric Turbidity Units
    total_dissolved_solids_ppm = Column(Float, nullable=True)  # TDS
    chlorine_ppm = Column(Float, nullable=True)
    dissolved_oxygen_ppm = Column(Float, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    bacterial_count_cfu_ml = Column(Float, nullable=True)  # Colony Forming Units
    contamination_detected = Column(Boolean, default=False)
    contamination_type = Column(String(200), nullable=True)
    contaminant_level_ppm = Column(Float, nullable=True)
    overall_quality_status = Column(String(50), default="good")  # "good", "fair", "poor", "contaminated"
    created_at = Column(DateTime, default=datetime.utcnow)


class WaterRecyclingLoop(Base):
    __tablename__ = "water_recycling_loops"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    loop_name = Column(String(200), nullable=False)
    loop_type = Column(String(100), nullable=False)  # e.g., "greywater_reuse", "condensate_recovery", "runoff_capture"
    source_system = Column(String(200), nullable=True)
    destination_system = Column(String(200), nullable=True)
    active = Column(Boolean, default=True)
    daily_recycled_liters = Column(Float, default=0.0)
    total_recycled_liters = Column(Float, default=0.0)
    efficiency_percent = Column(Float, default=85.0)
    last_cycle = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
