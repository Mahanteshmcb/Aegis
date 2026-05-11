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
    scheduled_tasks = relationship("ScheduledRoboticTask", back_populates="tenant")
    system_alerts = relationship("SystemAlert", back_populates="tenant")
    robot_health_snapshots = relationship("RobotHealthSnapshot", back_populates="tenant")
    system_performance_metrics = relationship("SystemPerformanceMetric", back_populates="tenant")
    emergency_events = relationship("EmergencyEvent", back_populates="tenant")
    backup_power_states = relationship("BackupPowerState", back_populates="tenant")
    data_backup_snapshots = relationship("DataBackupSnapshot", back_populates="tenant")
    data_sync_jobs = relationship("DataSyncJob", back_populates="tenant")


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


class ScheduledRoboticTask(Base):
    __tablename__ = "scheduled_robotic_tasks"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    operation_type = Column(String(100), nullable=False)
    requested_robot_id = Column(String(100), nullable=True)
    assigned_robot_id = Column(String(100), nullable=True)
    zone_id = Column(String(100), nullable=True)
    priority = Column(Integer, default=5, nullable=False)
    task_detail = Column(JSON, default=dict)
    task_metadata = Column("metadata", JSON, default=dict)
    timeout_seconds = Column(Integer, default=60)
    status = Column(String(50), default="pending")
    conflict_reason = Column(String(255), nullable=True)
    enqueue_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="scheduled_tasks")


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
Tenant.scheduled_tasks = relationship("ScheduledRoboticTask", back_populates="tenant")


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


# ============================================================================
# DAY 45: SUCCESSION PLANNING MODELS - Crop Rotation, Companion Planting, Seasonal Planning
# ============================================================================

class CropRotationPlan(Base):
    """
    Complete crop rotation plan for a spatial zone based on syntropic agriculture principles.
    Tracks crop sequences, timing, and predicted outcomes.
    """
    __tablename__ = "crop_rotation_plans"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    spatial_zone_id = Column(Integer, ForeignKey("spatial_zones.id"), nullable=False, index=True)

    # Plan details
    plan_name = Column(String(255), nullable=False)
    description = Column(Text)
    plan_version = Column(Integer, default=1)

    # Rotation sequence
    crop_sequence = Column(JSON, nullable=False)  # List of crop IDs in order
    years = Column(Integer, nullable=False)  # Length of rotation cycle

    # Timing
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime)

    # Projected outcomes
    soil_health_projection = Column(Float)  # 0-1 projected soil health at end
    predicted_avg_yield = Column(Float)  # kg expected yield per year
    biodiversity_score = Column(Float)  # 0-1 genetic diversity metric
    estimated_revenue = Column(Float)  # $ estimated economic value

    # Plan status
    is_active = Column(Boolean, default=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255))  # User who approved
    approval_date = Column(DateTime)

    # Metadata
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id])
    spatial_zone = relationship("SpatialZone", foreign_keys=[spatial_zone_id])
    seasonal_schedules = relationship("SeasonalPlantingSchedule", back_populates="rotation_plan")
    companion_pairings = relationship("CompanionPlanting", back_populates="rotation_plan")


class SeasonalPlantingSchedule(Base):
    """
    Seasonal planting schedule for a specific crop in a rotation plan.
    Maps crops to seasons and months for optimal growing conditions.
    """
    __tablename__ = "seasonal_planting_schedules"

    id = Column(Integer, primary_key=True, index=True)
    rotation_plan_id = Column(Integer, ForeignKey("crop_rotation_plans.id"), nullable=False, index=True)

    # Planting details
    year_in_rotation = Column(Integer, nullable=False)  # Year 1, 2, 3, etc.
    species_id = Column(Integer, ForeignKey("biological_species.id"), nullable=False, index=True)
    crop_name = Column(String(255))  # Cached for convenience

    # Seasonal timing
    preferred_season = Column(String(50), nullable=False)  # "spring", "summer", "fall", "winter"
    start_month = Column(Integer)  # 1-12
    end_month = Column(Integer)  # 1-12
    expected_duration_days = Column(Integer)  # Growth duration

    # Planting parameters
    density_per_m2 = Column(Float)  # Seedlings per m²
    spacing_cm = Column(Float)  # Distance between plants
    vertical_layer = Column(String(20))  # "ground", "mid_canopy", "upper"

    # Companion planting for this crop in this year
    companion_crops = Column(JSON, default=list)  # Species IDs of companions
    incompatible_crops = Column(JSON, default=list)  # Species IDs to avoid

    # Expected outcomes
    expected_yield_kg = Column(Float)
    water_requirement_liters = Column(Float)
    nutrient_requirements = Column(JSON, default=dict)  # {"N": 50, "P": 30, "K": 40}

    # Status
    is_planned = Column(Boolean, default=False)
    is_planted = Column(Boolean, default=False)
    is_harvested = Column(Boolean, default=False)
    actual_yield_kg = Column(Float)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rotation_plan = relationship("CropRotationPlan", back_populates="seasonal_schedules")
    species = relationship("BiologicalSpecies", foreign_keys=[species_id])


class CompanionPlanting(Base):
    """
    Companion planting relationships within rotation plans.
    Tracks beneficial and antagonistic crop pairings.
    """
    __tablename__ = "companion_plantings"

    id = Column(Integer, primary_key=True, index=True)
    rotation_plan_id = Column(Integer, ForeignKey("crop_rotation_plans.id"), nullable=False, index=True)

    # Crop pairing
    crop_a_species_id = Column(Integer, ForeignKey("biological_species.id"), nullable=False, index=True)
    crop_b_species_id = Column(Integer, ForeignKey("biological_species.id"), nullable=False, index=True)

    # Relationship details
    relationship_type = Column(String(50), nullable=False)  # "beneficial", "antagonistic", "neutral"
    compatibility_score = Column(Float)  # -1 (incompatible) to 1 (highly compatible)

    # Reasons for pairing
    reason = Column(Text)  # "N-fixer supports heavy feeder", etc.
    benefits = Column(JSON, default=list)  # List of benefits
    risks = Column(JSON, default=list)  # List of risks if incompatible

    # Spatial arrangement
    distance_cm = Column(Float)  # Optimal distance between crops
    arrangement_pattern = Column(String(50))  # "row", "mixed", "intercrop", "border"

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    rotation_plan = relationship("CropRotationPlan", back_populates="companion_pairings")
    crop_a = relationship("BiologicalSpecies", foreign_keys=[crop_a_species_id])
    crop_b = relationship("BiologicalSpecies", foreign_keys=[crop_b_species_id])


# ============================================================================
# DAY 47: REAL-TIME MONITORING DASHBOARD MODELS
# ============================================================================

class SystemAlert(Base):
    """
    System alerts for monitoring robotic fleet health and anomalies.
    Tracks alerts from robot health issues to system-wide problems.
    """
    __tablename__ = "system_alerts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Alert details
    alert_type = Column(String(100), nullable=False, index=True)  # "robot_health", "fleet_efficiency", "safety_incident", "system_error"
    severity = Column(String(20), nullable=False, index=True)  # "low", "medium", "high", "critical"
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(255), nullable=False, index=True)  # robot_id, zone_id, or "system"

    # Alert data and context
    data = Column(JSON, default=dict)  # Additional alert-specific data

    # Acknowledgment tracking
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="system_alerts")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])


class RobotHealthSnapshot(Base):
    """
    Periodic snapshots of robot health status for monitoring and analytics.
    Captures key health metrics at regular intervals.
    """
    __tablename__ = "robot_health_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Robot identification
    robot_id = Column(String(100), nullable=False, index=True)

    # Health status
    status = Column(String(50), nullable=False)  # "healthy", "warning", "critical", "offline"

    # System metrics
    battery_level = Column(Float)  # Percentage 0-100
    cpu_usage_percent = Column(Float)  # CPU utilization 0-100
    memory_usage_percent = Column(Float)  # Memory utilization 0-100
    temperature_c = Column(Float)  # Temperature in Celsius

    # Operational metrics
    uptime_seconds = Column(Integer)  # Seconds since last restart
    error_count = Column(Integer, default=0)  # Errors in current session
    warning_count = Column(Integer, default=0)  # Warnings in current session

    # Position and task info
    position = Column(JSON)  # {"x": float, "y": float, "z": float}
    current_task = Column(String(255))  # Current task ID if assigned

    # Metadata
    firmware_version = Column(String(100))
    last_seen = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="robot_health_snapshots")


class SystemPerformanceMetric(Base):
    """
    System-wide performance metrics for monitoring dashboard.
    Tracks fleet efficiency, safety scores, and operational KPIs.
    """
    __tablename__ = "system_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)  # "fleet_efficiency", "safety_score", "task_completion_rate"
    metric_category = Column(String(50), nullable=False)  # "efficiency", "safety", "productivity", "health"

    # Metric value
    value = Column(Float, nullable=False)
    unit = Column(String(50))  # "%", "count", "seconds", "kg", etc.

    # Time period
    timestamp = Column(DateTime, nullable=False, index=True)
    period_minutes = Column(Integer, default=60)  # Aggregation period in minutes

    # Context data
    context_data = Column(JSON, default=dict)  # Additional metric-specific data

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="system_performance_metrics")


# ============================================================================
# DAY 48: EMERGENCY RESPONSE PROTOCOL MODELS
# ============================================================================

class EmergencyEvent(Base):
    """
    Records of emergency events and their triggered responses.
    Tracks system failures and recovery procedures.
    """
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)

    # Event identification
    event_id = Column(String(100), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)  # "critical_failure", "power_loss", "network_failure", "system_overload", "security_breach"
    severity = Column(String(20), nullable=False)  # "warning", "critical", "catastrophic"
    description = Column(Text, nullable=False)

    # Trigger information
    triggered_by = Column(String(255))  # "automated", "manual_override", "system_alert", etc.
    triggered_by_user = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Emergency status
    status = Column(String(50), default="active", index=True)  # "active", "recovering", "resolved", "failed"
    response_timestamp = Column(DateTime, default=datetime.utcnow)
    resolution_timestamp = Column(DateTime, nullable=True)

    # Emergency data
    affected_systems = Column(JSON, default=list)  # List of affected system names
    root_cause = Column(Text, nullable=True)
    event_metadata = Column("metadata", JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="emergency_events")
    triggered_user = relationship("User", foreign_keys=[triggered_by_user])
    emergency_responses = relationship("EmergencyResponse", back_populates="event")
    power_states = relationship("BackupPowerState", back_populates="event")


class EmergencyResponse(Base):
    """
    Automated emergency response actions taken in response to system failures.
    """
    __tablename__ = "emergency_responses"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=False, index=True)

    # Response details
    action_type = Column(String(100), nullable=False)  # "fleet_stop", "safe_shutdown", "power_failover", "system_isolation", "manual_override"
    action_name = Column(String(255), nullable=False)
    description = Column(Text)

    # Response status
    status = Column(String(50), default="pending")  # "pending", "executing", "completed", "failed"
    priority = Column(Integer, default=0)  # Execution priority (higher = first)

    # Affected resources
    affected_robots = Column(JSON, default=list)  # Robot IDs affected by this response
    affected_zones = Column(JSON, default=list)  # Zone IDs affected
    affected_tasks = Column(JSON, default=list)  # Task IDs cancelled/modified

    # Response timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    # Results and metadata
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    result_data = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("EmergencyEvent", back_populates="emergency_responses")


class BackupPowerState(Base):
    """
    Tracks backup power system status and transitions.
    """
    __tablename__ = "backup_power_states"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=True, index=True)

    # Power state
    is_active = Column(Boolean, default=False, index=True)
    power_mode = Column(String(50), default="normal")  # "normal", "battery", "solar", "generator", "manual"

    # Battery information
    battery_level_percent = Column(Float)  # Current battery level
    battery_capacity_wh = Column(Float)  # Total capacity
    estimated_runtime_hours = Column(Float)  # Estimated hours remaining

    # Solar information
    solar_generation_w = Column(Float)  # Current solar generation
    solar_max_capacity_w = Column(Float)  # Max solar capacity

    # Load information
    current_load_w = Column(Float)  # Current power consumption
    max_load_w = Column(Float)  # Max sustainable load

    # Transition details
    transition_timestamp = Column(DateTime, default=datetime.utcnow)
    transition_reason = Column(String(255))
    transition_duration_ms = Column(Integer)  # Time taken for transition

    # Recovery info
    recovery_status = Column(String(50), default="pending")  # "pending", "in_progress", "completed", "failed"
    recovery_eta_seconds = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="backup_power_states")
    event = relationship("EmergencyEvent", back_populates="power_states")


class DataBackupSnapshot(Base):
    """
    Tracks offline backup snapshots and integrity verification state.
    """
    __tablename__ = "data_backup_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=True, index=True)
    snapshot_id = Column(String(255), unique=True, nullable=False, index=True)
    source = Column(String(255), nullable=False)
    record_count = Column(Integer, default=0)
    data_hash = Column(String(255), nullable=False)
    storage_uri = Column(String(1024), nullable=False)
    status = Column(String(50), default="created")
    integrity_verified = Column(Boolean, default=False)
    verification_hash = Column(String(255), nullable=True)
    verification_notes = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    tenant = relationship("Tenant", back_populates="data_backup_snapshots")
    event = relationship("EmergencyEvent", foreign_keys=[event_id])


class DataSyncJob(Base):
    """
    Tracks offline synchronization jobs between systems.
    """
    __tablename__ = "data_sync_jobs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    sync_id = Column(String(255), unique=True, nullable=False, index=True)
    source_system = Column(String(255), nullable=False)
    target_system = Column(String(255), nullable=False)
    status = Column(String(50), default="pending")
    attempt_count = Column(Integer, default=0)
    payload_hash = Column(String(255), nullable=True)
    result_summary = Column(Text, nullable=True)
    last_attempt = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="data_sync_jobs")


class RecoveryProcedure(Base):
    """
    Recovery procedures to restore normal operations after emergency.
    """
    __tablename__ = "recovery_procedures"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("emergency_events.id"), nullable=False, index=True)

    # Procedure details
    procedure_name = Column(String(255), nullable=False)
    procedure_type = Column(String(100), nullable=False)  # "system_restart", "fleet_reboot", "data_recovery", "sensor_recalibration", "network_reset"
    description = Column(Text)

    # Execution status
    status = Column(String(50), default="pending")  # "pending", "in_progress", "completed", "failed", "rolled_back"
    estimated_duration_minutes = Column(Integer)
    actual_duration_minutes = Column(Integer, nullable=True)

    # Procedure steps
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    current_step = Column(String(255), nullable=True)

    # Results
    success = Column(Boolean, default=False)
    validation_passed = Column(Boolean, default=False)
    error_log = Column(Text, nullable=True)
    rollback_performed = Column(Boolean, default=False)

    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("EmergencyEvent", foreign_keys=[event_id])


class CropSuccessionHistory(Base):
    """
    Historical record of crop plantings in zones for rotation tracking.
    Ensures minimum rotation requirements are met.
    """
    __tablename__ = "crop_succession_history"

    id = Column(Integer, primary_key=True, index=True)
    spatial_zone_id = Column(Integer, ForeignKey("spatial_zones.id"), nullable=False, index=True)
    species_id = Column(Integer, ForeignKey("biological_species.id"), nullable=False, index=True)

    # Historical planting
    planting_date = Column(DateTime, nullable=False, index=True)
    harvest_date = Column(DateTime)
    harvest_yield_kg = Column(Float)

    # Succession record
    years_since_planting = Column(Integer)  # Calculated years
    meets_rotation_requirement = Column(Boolean)  # Minimum years satisfied?
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    spatial_zone = relationship("SpatialZone", foreign_keys=[spatial_zone_id])
    species = relationship("BiologicalSpecies", foreign_keys=[species_id])
