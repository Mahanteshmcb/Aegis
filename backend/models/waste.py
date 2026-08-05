"""
Waste management models: sorting, composting, recycling, and hazardous waste containment.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base


class WasteContainer(Base):
    __tablename__ = "waste_containers"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    container_name = Column(String(200), nullable=False)
    waste_type = Column(String(100), nullable=False)  # "organic", "recyclable", "hazardous", "inert"
    capacity_kg = Column(Float, nullable=False)
    current_load_kg = Column(Float, default=0.0)
    location = Column(String(200), nullable=True)
    active = Column(Boolean, default=True)
    last_emptied = Column(DateTime, nullable=True)
    emptying_frequency_days = Column(Integer, default=7)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WasteSortingLog(Base):
    __tablename__ = "waste_sorting_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    waste_stream_id = Column(Integer, nullable=True)
    waste_type = Column(String(100), nullable=False)
    weight_kg = Column(Float, nullable=False)
    source_location = Column(String(200), nullable=True)
    destination_container = Column(String(200), nullable=True)
    sorting_method = Column(String(100), nullable=False)  # "automated", "manual", "hybrid"
    contamination_detected = Column(Boolean, default=False)
    contamination_type = Column(String(200), nullable=True)
    quality_score = Column(Float, nullable=True)  # 0-100
    processed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class CompostingProcess(Base):
    __tablename__ = "composting_processes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    process_name = Column(String(200), nullable=False)
    pile_id = Column(String(100), nullable=False)
    status = Column(String(50), default="preparing")  # "preparing", "active", "curing", "completed"
    organic_input_kg = Column(Float, default=0.0)
    current_weight_kg = Column(Float, default=0.0)
    moisture_percent = Column(Float, nullable=True)
    temperature_celsius = Column(Float, nullable=True)
    carbon_nitrogen_ratio = Column(Float, nullable=True)
    stage = Column(String(50), nullable=True)  # "thermophilic", "mesophilic", "maturation"
    started_at = Column(DateTime, nullable=True)
    expected_completion = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    compost_output_kg = Column(Float, default=0.0)
    pathogen_tested = Column(Boolean, default=False)
    pathogen_safe = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RecyclingProcess(Base):
    __tablename__ = "recycling_processes"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    process_name = Column(String(200), nullable=False)
    material_type = Column(String(100), nullable=False)  # "plastic", "metal", "glass", "paper", "electronics"
    input_weight_kg = Column(Float, default=0.0)
    current_weight_kg = Column(Float, default=0.0)
    status = Column(String(50), default="pending")  # "pending", "sorting", "processing", "completed"
    recovery_rate_percent = Column(Float, default=0.0)
    output_material_type = Column(String(100), nullable=True)
    output_weight_kg = Column(Float, default=0.0)
    destination_facility = Column(String(200), nullable=True)
    processing_method = Column(String(100), nullable=True)  # "mechanical", "chemical", "thermal"
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    cost_per_kg = Column(Float, nullable=True)
    environmental_impact_score = Column(Float, nullable=True)  # Estimated CO2 saved (kg)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class HazardousWasteStorage(Base):
    __tablename__ = "hazardous_waste_storage"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    container_id = Column(String(100), nullable=False)
    chemical_name = Column(String(200), nullable=False)
    chemical_type = Column(String(100), nullable=False)  # "pesticide", "heavy_metal", "solvent", "radioactive", "biological"
    cas_number = Column(String(50), nullable=True)
    quantity_liters = Column(Float, nullable=False)
    concentration_percent = Column(Float, nullable=True)
    hazard_classification = Column(String(200), nullable=True)  # GHS classification
    physical_state = Column(String(50), nullable=False)  # "liquid", "solid", "gas", "powder"
    storage_location = Column(String(200), nullable=False)
    storage_temperature_min = Column(Float, nullable=True)
    storage_temperature_max = Column(Float, nullable=True)
    container_condition = Column(String(50), default="good")  # "good", "fair", "compromised"
    is_sealed = Column(Boolean, default=True)
    leak_detection_sensor = Column(Boolean, default=False)
    ventilation_required = Column(Boolean, default=False)
    last_inspected = Column(DateTime, nullable=True)
    inspection_interval_days = Column(Integer, default=30)
    disposal_scheduled = Column(DateTime, nullable=True)
    disposal_facility = Column(String(200), nullable=True)
    safety_data_sheet_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WasteProcessingLog(Base):
    __tablename__ = "waste_processing_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    operation_type = Column(String(100), nullable=False)  # "sorting", "composting", "recycling", "incineration", "landfill"
    waste_category = Column(String(100), nullable=False)
    input_weight_kg = Column(Float, nullable=False)
    output_weight_kg = Column(Float, nullable=True)
    processing_efficiency_percent = Column(Float, nullable=True)
    energy_consumed_kwh = Column(Float, nullable=True)
    emissions_kg_co2 = Column(Float, nullable=True)
    processing_time_hours = Column(Float, nullable=True)
    operator = Column(String(200), nullable=True)
    notes = Column(Text, nullable=True)
    completed_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


class WasteMetrics(Base):
    __tablename__ = "waste_metrics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)
    metric_date = Column(DateTime, default=datetime.utcnow)
    total_waste_collected_kg = Column(Float, default=0.0)
    organic_waste_kg = Column(Float, default=0.0)
    recyclable_waste_kg = Column(Float, default=0.0)
    hazardous_waste_kg = Column(Float, default=0.0)
    inert_waste_kg = Column(Float, default=0.0)
    compost_produced_kg = Column(Float, default=0.0)
    recycled_material_kg = Column(Float, default=0.0)
    landfill_waste_kg = Column(Float, default=0.0)
    recycling_rate_percent = Column(Float, default=0.0)
    waste_diversion_rate_percent = Column(Float, default=0.0)
    total_emissions_kg_co2 = Column(Float, default=0.0)
    cost_per_kg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
