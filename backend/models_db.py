from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, JSON, Float, Text, Boolean
from sqlalchemy.orm import relationship

from backend.database import Base



class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    settings = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sensors = relationship("Sensor", back_populates="tenant")
    zones = relationship("Zone", back_populates="tenant")
    users = relationship("User", back_populates="tenant")
    audit_logs = relationship("AuditLog", back_populates="tenant")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")



class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    type = Column(String(100))
    location = Column(String(255))
    last_reading = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="sensors")
    audit_logs = relationship("AuditLog", back_populates="sensor")
    data_points = relationship("SensorData", back_populates="sensor")



class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255))
    location = Column(String(255))
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="zones")



class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    event_type = Column(String(100))
    data_hash = Column(String(255))
    blockchain_tx = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="audit_logs")
    sensor = relationship("Sensor", back_populates="audit_logs")


class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    unit = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    sensor = relationship("Sensor", back_populates="data_points")


# ============================================================================
# DAY 33: 3D SPATIAL MAPPING MODELS
# ============================================================================

class BiologicalSpecies(Base):
    """
    Database model for tracking 3,000+ biological crop species.
    Supports taxonomic classification, growth characteristics, and spatial requirements.
    """
    __tablename__ = "biological_species"

    id = Column(Integer, primary_key=True, index=True)
    scientific_name = Column(String(255), nullable=False, unique=True, index=True)  # e.g., "Solanum lycopersicum"
    common_name = Column(String(255), nullable=False, index=True)  # e.g., "Tomato"
    family = Column(String(100), index=True)  # e.g., "Solanaceae"
    genus = Column(String(100), index=True)  # e.g., "Solanum"
    species = Column(String(100), index=True)  # e.g., "lycopersicum"

    # Growth characteristics
    max_height_cm = Column(Float)  # Maximum height in centimeters
    canopy_radius_cm = Column(Float)  # Canopy spread radius
    root_depth_cm = Column(Float)  # Root system depth
    growth_cycle_days = Column(Integer)  # Days from planting to harvest
    vertical_layer = Column(String(20))  # "ground", "mid_canopy", "upper"

    # Environmental requirements
    optimal_temp_min_c = Column(Float)
    optimal_temp_max_c = Column(Float)
    optimal_humidity_percent = Column(Float)
    soil_ph_min = Column(Float)
    soil_ph_max = Column(Float)
    light_requirement = Column(String(50))  # "full_sun", "partial_shade", "shade"

    # Companion planting relationships
    companion_species = Column(JSON, default=list)  # List of compatible species IDs
    antagonistic_species = Column(JSON, default=list)  # List of incompatible species IDs

    # Metadata
    description = Column(Text)
    nutritional_value = Column(JSON, default=dict)  # Nutritional profile
    medicinal_properties = Column(JSON, default=dict)  # Medicinal uses
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    crop_instances = relationship("CropInstance", back_populates="species")


class SpatialZone(Base):
    """
    3D spatial zone model for managing crop positioning and zone management.
    Supports vertical layering: ground, mid-canopy, upper levels.
    """
    __tablename__ = "spatial_zones"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # 3D bounding box coordinates (in meters, relative to estate origin)
    min_x = Column(Float, nullable=False)
    max_x = Column(Float, nullable=False)
    min_y = Column(Float, nullable=False)
    max_y = Column(Float, nullable=False)
    min_z = Column(Float, nullable=False, default=0.0)  # Ground level
    max_z = Column(Float, nullable=False, default=3.0)  # Upper canopy

    # Zone properties
    zone_type = Column(String(50))  # "growing_bed", "greenhouse", "outdoor", "vertical_farm"
    soil_type = Column(String(100))
    irrigation_type = Column(String(50))
    sunlight_exposure = Column(String(50))  # "full_sun", "partial", "shade"
    microclimate = Column(JSON, default=dict)  # Temperature, humidity zones

    # Vertical layers within this zone
    supports_ground_layer = Column(Boolean, default=True)
    supports_mid_canopy = Column(Boolean, default=True)
    supports_upper_canopy = Column(Boolean, default=False)

    # Management
    max_capacity = Column(Integer)  # Maximum number of crop instances
    current_occupancy = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="spatial_zones")
    crop_instances = relationship("CropInstance", back_populates="spatial_zone")


class CropInstance(Base):
    """
    Individual crop instance with precise 3D positioning.
    Tracks planting, growth, and harvesting of specific plants.
    """
    __tablename__ = "crop_instances"

    id = Column(Integer, primary_key=True, index=True)
    species_id = Column(Integer, ForeignKey("biological_species.id"), nullable=False, index=True)
    spatial_zone_id = Column(Integer, ForeignKey("spatial_zones.id"), nullable=False, index=True)

    # 3D positioning (precise coordinates within the spatial zone)
    position_x = Column(Float, nullable=False)  # X coordinate in meters
    position_y = Column(Float, nullable=False)  # Y coordinate in meters
    position_z = Column(Float, nullable=False)  # Z coordinate (height) in meters

    # Planting and lifecycle
    planting_date = Column(DateTime)
    expected_harvest_date = Column(DateTime)
    actual_harvest_date = Column(DateTime)
    harvest_yield_kg = Column(Float)

    # Growth tracking
    current_height_cm = Column(Float)
    health_status = Column(String(50), default="healthy")  # "healthy", "stressed", "diseased", "dead"
    growth_stage = Column(String(50))  # "seedling", "vegetative", "flowering", "fruiting", "mature"

    # Vertical layer assignment
    vertical_layer = Column(String(20), nullable=False)  # "ground", "mid_canopy", "upper"

    # Environmental conditions at planting
    planting_soil_ph = Column(Float)
    planting_soil_moisture = Column(Float)
    planting_temperature_c = Column(Float)

    # Maintenance tracking
    last_watered = Column(DateTime)
    last_fertilized = Column(DateTime)
    last_pruned = Column(DateTime)
    pest_incidents = Column(JSON, default=list)  # List of pest encounters

    # Metadata
    notes = Column(Text)
    batch_id = Column(String(100))  # For tracking seed batches
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    species = relationship("BiologicalSpecies", back_populates="crop_instances")
    spatial_zone = relationship("SpatialZone", back_populates="crop_instances")
    lifecycle_events = relationship("CropLifecycleEvent", back_populates="crop_instance")
    biological_metrics = relationship("BiologicalMetric", back_populates="crop_instance")


# Add relationships to existing models
Tenant.spatial_zones = relationship("SpatialZone", back_populates="tenant")


class VryndaraRequest(Base):
    __tablename__ = "vryndara_requests"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    agent = Column(String(100), nullable=False)
    request_type = Column(String(100), nullable=False)
    payload = Column(JSON)
    response = Column(JSON)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# DAY 41: AGRICULTURAL DATA MODELS - Crops, Metrics, and Specialized Sensors
# ============================================================================

class AgriculturalSensor(Base):
    """
    Specialized agricultural sensor types beyond standard environmental sensors.
    Tracks mycelial probes, acoustic monitors, spectral cameras, etc.
    """
    __tablename__ = "agricultural_sensors"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True, index=True)
    
    # Sensor type and specification
    sensor_type = Column(String(100), nullable=False, index=True)  # "mycelial_probe", "acoustic_pest_monitor", "ndvi_camera", "thermal_camera", "chlorophyll_meter"
    model = Column(String(255))
    manufacturer = Column(String(255))
    
    # Physical location
    location_x = Column(Float)  # Grid X coordinate (m)
    location_y = Column(Float)  # Grid Y coordinate (m)
    location_z = Column(Float)  # Height (m)
    
    # Sensor specifications
    measurement_unit = Column(String(50))  # "mg/g", "Hz", "SPAD", "°C", "ratio", etc.
    min_range = Column(Float)
    max_range = Column(Float)
    accuracy = Column(Float)  # ±% accuracy
    sampling_rate_hz = Column(Float)  # Samples per second
    
    # Status tracking
    is_active = Column(Boolean, default=True)
    last_calibration = Column(DateTime)
    battery_level = Column(Float)  # % (if battery-powered)
    signal_strength = Column(Float)  # dBm or % signal quality
    
    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    zone = relationship("Zone", foreign_keys=[zone_id])
    sensor_readings = relationship("AgriculturalSensorReading", back_populates="sensor")


class AgriculturalSensorReading(Base):
    """
    Time-series readings from agricultural sensors for biological metrics tracking.
    """
    __tablename__ = "agricultural_sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("agricultural_sensors.id"), nullable=False, index=True)
    
    # Reading data
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(50))
    
    # Data quality
    confidence = Column(Float)  # 0-1 confidence score
    is_anomaly = Column(Boolean, default=False)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    sensor = relationship("AgriculturalSensor", back_populates="sensor_readings")


class CropLifecycleEvent(Base):
    """
    Track crop lifecycle events: planting, growth stage transitions, pest detection, disease, harvest, etc.
    Supports traceability and compliance reporting.
    """
    __tablename__ = "crop_lifecycle_events"

    id = Column(Integer, primary_key=True, index=True)
    crop_instance_id = Column(Integer, ForeignKey("crop_instances.id"), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # "planting", "germination", "disease_detected", "pest_detected", "fertilized", "pruned", "harvested", "stage_transition"
    event_date = Column(DateTime, nullable=False, index=True)
    
    # Event data
    description = Column(Text)
    data = Column(JSON, default=dict)  # Event-specific data (pest name, disease type, fertilizer amount, etc.)
    
    # Action taken
    action_taken = Column(String(255))  # e.g., "Applied fungicide", "Pruned affected branches"
    action_date = Column(DateTime)
    
    # Blockchain record
    blockchain_tx = Column(String(255))  # Blockchain transaction hash for immutability
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    crop_instance = relationship("CropInstance", back_populates="lifecycle_events")


class BiologicalMetric(Base):
    """
    Aggregated biological and health metrics for crop instances.
    Stores computed metrics from ML models and sensor fusion.
    """
    __tablename__ = "biological_metrics"

    id = Column(Integer, primary_key=True, index=True)
    crop_instance_id = Column(Integer, ForeignKey("crop_instances.id"), nullable=False, index=True)
    
    # Time period for aggregation
    measurement_date = Column(DateTime, nullable=False, index=True)
    
    # ML Model Predictions (from orchestrator engines)
    health_score = Column(Float)  # Visual crop health: 0-1
    health_status = Column(String(50))  # "HEALTHY", "STRESS_EARLY", "STRESS_MODERATE", "STRESS_SEVERE", "DISEASE", "CRITICAL"
    
    ndvi = Column(Float)  # Normalized Difference Vegetation Index
    chlorophyll_content = Column(Float)  # SPAD units
    canopy_coverage_percent = Column(Float)
    leaf_area_index = Column(Float)  # m²/m²
    
    # Soil Metrics (from mycelial sensors)
    nitrogen_level = Column(Float)  # Normalized 0-1
    phosphorus_level = Column(Float)  # Normalized 0-1
    potassium_level = Column(Float)  # Normalized 0-1
    soil_health_status = Column(String(50))  # "OPTIMAL", "SUBOPTIMAL", "DEFICIENT", "CRITICAL"
    
    # Pest and Disease Detection (from acoustic/visual monitors)
    pest_detected = Column(Boolean, default=False)
    pest_types = Column(JSON, default=list)  # List of detected pest names
    pest_severity = Column(String(50))  # "none", "low", "moderate", "high", "critical"
    
    disease_detected = Column(Boolean, default=False)
    disease_types = Column(JSON, default=list)  # List of detected disease names
    disease_severity = Column(String(50))  # "none", "low", "moderate", "high", "critical"
    
    # Growth and Development
    height_cm = Column(Float)
    stem_diameter_cm = Column(Float)
    leaf_count = Column(Integer)
    flower_count = Column(Integer)
    fruit_count = Column(Integer)
    
    # Environmental conditions
    temperature_avg_c = Column(Float)
    humidity_avg_percent = Column(Float)
    soil_moisture_percent = Column(Float)
    light_hours = Column(Float)  # Daily light exposure hours
    
    # Recommendations from ML models
    recommendations = Column(JSON, default=dict)  # Priority actions needed
    
    # Data quality
    data_sources = Column(JSON, default=list)  # Sensors/models used for this metric
    confidence_score = Column(Float)  # 0-1 confidence in aggregated metrics
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    crop_instance = relationship("CropInstance", back_populates="biological_metrics")
