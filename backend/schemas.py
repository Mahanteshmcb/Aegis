from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class TenantBase(BaseModel):
    name: str
    settings: Optional[Dict[str, Any]] = {}


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class Tenant(TenantBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class SensorBase(BaseModel):
    type: Optional[str] = None
    location: Optional[str] = None


class SensorCreate(SensorBase):
    tenant_id: int


class SensorUpdate(SensorBase):
    last_reading: Optional[Any] = None


class Sensor(SensorBase):
    id: int
    tenant_id: int
    last_reading: Optional[Any] = None
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class AuditLogBase(BaseModel):
    tenant_id: Optional[int] = None
    sensor_id: Optional[int] = None
    event_type: str
    data_hash: str
    blockchain_tx: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ScheduledTaskBase(BaseModel):
    task_id: str
    operation_type: str
    requested_robot_id: Optional[str] = None
    assigned_robot_id: Optional[str] = None
    zone_id: Optional[str] = None
    priority: int = 5
    task_detail: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}
    timeout_seconds: int = 60
    status: str = "pending"
    conflict_reason: Optional[str] = None
    enqueue_time: Optional[datetime] = None
    assigned_time: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ScheduledTaskCreate(ScheduledTaskBase):
    pass


class ScheduledTaskResponse(ScheduledTaskBase):
    id: int
    tenant_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class AgriculturalSensorBase(BaseModel):
    tenant_id: int
    zone_id: Optional[int] = None
    sensor_type: str
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    location_z: Optional[float] = None
    measurement_unit: Optional[str] = None
    min_range: Optional[float] = None
    max_range: Optional[float] = None
    accuracy: Optional[float] = None
    sampling_rate_hz: Optional[float] = None
    is_active: Optional[bool] = True
    last_calibration: Optional[datetime] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    notes: Optional[str] = None


class AgriculturalSensorCreate(AgriculturalSensorBase):
    pass


class AgriculturalSensorResponse(AgriculturalSensorBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class AgriculturalSensorReadingBase(BaseModel):
    sensor_id: int
    timestamp: datetime
    value: float
    unit: Optional[str] = None
    confidence: Optional[float] = None
    is_anomaly: Optional[bool] = False
    notes: Optional[str] = None


class AgriculturalSensorReadingCreate(AgriculturalSensorReadingBase):
    pass


class AgriculturalSensorReadingResponse(AgriculturalSensorReadingBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class CropLifecycleEventBase(BaseModel):
    event_type: str
    event_date: datetime
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    action_taken: Optional[str] = None
    action_date: Optional[datetime] = None
    blockchain_tx: Optional[str] = None


class CropLifecycleEventCreate(CropLifecycleEventBase):
    pass


class CropLifecycleEventResponse(CropLifecycleEventBase):
    id: int
    crop_instance_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class BiologicalMetricBase(BaseModel):
    measurement_date: datetime
    health_score: Optional[float] = None
    health_status: Optional[str] = None
    ndvi: Optional[float] = None
    chlorophyll_content: Optional[float] = None
    canopy_coverage_percent: Optional[float] = None
    leaf_area_index: Optional[float] = None
    nitrogen_level: Optional[float] = None
    phosphorus_level: Optional[float] = None
    potassium_level: Optional[float] = None
    soil_health_status: Optional[str] = None
    pest_detected: Optional[bool] = False
    pest_types: Optional[List[str]] = None
    pest_severity: Optional[str] = None
    disease_detected: Optional[bool] = False
    disease_types: Optional[List[str]] = None
    disease_severity: Optional[str] = None
    height_cm: Optional[float] = None
    stem_diameter_cm: Optional[float] = None
    leaf_count: Optional[int] = None
    flower_count: Optional[int] = None
    fruit_count: Optional[int] = None
    temperature_avg_c: Optional[float] = None
    humidity_avg_percent: Optional[float] = None
    soil_moisture_percent: Optional[float] = None
    light_hours: Optional[float] = None
    recommendations: Optional[Dict[str, Any]] = None
    data_sources: Optional[List[str]] = None
    confidence_score: Optional[float] = None


class BiologicalMetricCreate(BiologicalMetricBase):
    pass


class BiologicalMetricResponse(BiologicalMetricBase):
    id: int
    crop_instance_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class CropInstanceBase(BaseModel):
    species_id: int
    spatial_zone_id: int
    position_x: float
    position_y: float
    position_z: float
    vertical_layer: str
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    planting_soil_ph: Optional[float] = None
    planting_soil_moisture: Optional[float] = None
    planting_temperature_c: Optional[float] = None
    batch_id: Optional[str] = None
    notes: Optional[str] = None
    current_height_cm: Optional[float] = None
    health_status: Optional[str] = None
    growth_stage: Optional[str] = None
    last_watered: Optional[datetime] = None
    last_fertilized: Optional[datetime] = None
    last_pruned: Optional[datetime] = None
    pest_incidents: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = True
    harvest_yield_kg: Optional[float] = None


class CropInstanceCreate(CropInstanceBase):
    pass


class CropInstanceUpdate(BaseModel):
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    position_z: Optional[float] = None
    vertical_layer: Optional[str] = None
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    actual_harvest_date: Optional[datetime] = None
    planting_soil_ph: Optional[float] = None
    planting_soil_moisture: Optional[float] = None
    planting_temperature_c: Optional[float] = None
    batch_id: Optional[str] = None
    notes: Optional[str] = None
    current_height_cm: Optional[float] = None
    health_status: Optional[str] = None
    growth_stage: Optional[str] = None
    last_watered: Optional[datetime] = None
    last_fertilized: Optional[datetime] = None
    last_pruned: Optional[datetime] = None
    pest_incidents: Optional[List[Dict[str, Any]]] = None
    is_active: Optional[bool] = None
    harvest_yield_kg: Optional[float] = None


class CropInstanceResponse(CropInstanceBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


# --- User schemas for authentication and RBAC ---
class UserBase(BaseModel):
    email: EmailStr
    role: str = "viewer"

class UserCreate(UserBase):
    password: str
    tenant_id: int

class UserRead(UserBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
        from_attributes = True

class UserProfile(UserBase):
    id: int
    tenant_id: int

    class Config:
        orm_mode = True

class UserInDB(UserRead):
    hashed_password: str


# --- Monitoring and Alerting Schemas ---

class RobotHealthStatus(BaseModel):
    robot_id: str
    status: str  # "healthy", "warning", "critical", "offline"
    battery_level: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    memory_usage_percent: Optional[float] = None
    temperature_c: Optional[float] = None
    last_seen: Optional[datetime] = None
    uptime_seconds: Optional[int] = None
    error_count: Optional[int] = None
    warning_count: Optional[int] = None
    position: Optional[Dict[str, float]] = None
    current_task: Optional[str] = None
    firmware_version: Optional[str] = None


class SystemAlertBase(BaseModel):
    alert_type: str  # "robot_health", "fleet_efficiency", "safety_incident", "system_error"
    severity: str  # "low", "medium", "high", "critical"
    title: str
    message: str
    source: str  # robot_id, zone_id, or "system"
    data: Optional[Dict[str, Any]] = {}
    acknowledged: bool = False
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None


class SystemAlertCreate(SystemAlertBase):
    tenant_id: int


class SystemAlertResponse(SystemAlertBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class RealTimeStatusResponse(BaseModel):
    timestamp: datetime
    system_health: str  # "healthy", "degraded", "critical"
    fleet_status: FleetStatusResponse
    robot_health: List[RobotHealthStatus]
    active_alerts: List[SystemAlertResponse]
    performance_metrics: Dict[str, Any]
    last_updated: datetime


class MonitoringDashboardResponse(BaseModel):
    real_time_status: RealTimeStatusResponse
    historical_data: Dict[str, Any]
    alerts_summary: Dict[str, Any]
    recommendations: List[str]


# --- Robotics Schemas ---

class Coordinate3D(BaseModel):
    x: float
    y: float
    z: float

class NavigationTarget(BaseModel):
    destination: Coordinate3D
    waypoints: Optional[List[Coordinate3D]] = []
    speed_percent: Optional[float] = 50.0
    use_obstacles_map: Optional[bool] = False

class NavigationCommandRequest(BaseModel):
    command_id: str
    robot_id: str
    destination: Coordinate3D
    waypoints: Optional[List[Coordinate3D]] = []
    speed_percent: Optional[float] = 50.0
    use_obstacles_map: Optional[bool] = False
    timeout_seconds: Optional[int] = 60
    zone_id: Optional[str] = None

class RoboticTaskRequest(BaseModel):
    task_id: str
    robot_id: str
    operation_type: str
    priority: Optional[int] = 5
    task_detail: Optional[Dict[str, Any]] = {}
    timeout_seconds: Optional[int] = 60
    metadata: Optional[Dict[str, str]] = {}

class SensorDataPayload(BaseModel):
    robot_id: str
    health: Dict[str, Any]
    environment: Dict[str, Any]
    observations: Optional[List[str]] = []
    timestamp_ms: Optional[int] = None

class FleetCoordinationRequest(BaseModel):
    task_type: str  # "HARVEST", "PLANT", "SPRAY", "INSPECT", "MAINTAIN"
    zone_id: str
    priority: Optional[int] = 5
    robot_count: Optional[int] = 1
    task_parameters: Optional[Dict[str, Any]] = None

class FleetOptimizationRequest(BaseModel):
    zone_id: str
    optimization_criteria: Dict[str, Any]  # e.g., {"efficiency": 0.8, "safety": 0.9, "energy": 0.7}

class EmergencyFleetStopRequest(BaseModel):
    zone_id: Optional[str] = None
    reason: Optional[str] = "manual_override"

class FleetStatusResponse(BaseModel):
    total_robots: int
    active_robots: int
    idle_robots: int
    robots_in_maintenance: int
    active_tasks: int
    queued_tasks: int
    safety_incidents: int
    last_safety_check: int
    fleet_efficiency_percent: float
    zone_status: Dict[str, Dict[str, Any]]

class FleetCoordinationResponse(BaseModel):
    task_id: str
    assigned_robots: List[str]
    coordination_status: str
    estimated_completion_minutes: int
    safety_protocols_active: bool
    collision_avoidance_active: bool
    load_balancing_active: bool

class FleetOptimizationResponse(BaseModel):
    optimization_id: str
    zone_id: str
    recommended_deployments: List[Dict[str, Any]]
    efficiency_gain_percent: float
    safety_score: float
    energy_savings_percent: float

class EmergencyFleetStopResponse(BaseModel):
    emergency_stop_issued: bool
    affected_robots: List[str]
    reason: str
    timestamp_ms: int
    safety_protocols_engaged: bool


# --- Emergency Response Schemas ---

class EmergencyEventBase(BaseModel):
    event_type: str
    severity: str  # "warning", "critical", "catastrophic"
    description: str
    triggered_by: Optional[str] = "automated"
    affected_systems: Optional[List[str]] = []
    root_cause: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class EmergencyEventCreate(EmergencyEventBase):
    pass


class EmergencyEventResponse(EmergencyEventBase):
    id: int
    event_id: str
    tenant_id: int
    status: str
    response_timestamp: datetime
    resolution_timestamp: Optional[datetime]
    triggered_by_user: Optional[int]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, alias="event_metadata")

    class Config:
        orm_mode = True
        allow_population_by_field_name = True


class EmergencyResponseBase(BaseModel):
    action_type: str
    action_name: str
    description: Optional[str] = None
    priority: Optional[int] = 0
    affected_robots: Optional[List[str]] = []
    affected_zones: Optional[List[str]] = []
    affected_tasks: Optional[List[str]] = []


class EmergencyResponseCreate(EmergencyResponseBase):
    pass


class EmergencyResponseResponse(EmergencyResponseBase):
    id: int
    event_id: int
    status: str
    initiated_at: datetime
    completed_at: Optional[datetime]
    execution_time_ms: Optional[int]
    success: bool
    error_message: Optional[str]
    result_data: Dict[str, Any]
    created_at: datetime

    class Config:
        orm_mode = True


class BackupPowerStateBase(BaseModel):
    is_active: bool
    power_mode: str  # "normal", "battery", "solar", "generator", "manual"
    battery_level_percent: Optional[float] = None
    estimated_runtime_hours: Optional[float] = None
    solar_generation_w: Optional[float] = None
    current_load_w: Optional[float] = None
    recovery_status: Optional[str] = "pending"
    recovery_eta_seconds: Optional[int] = None


class BackupPowerStateCreate(BackupPowerStateBase):
    event_id: Optional[int] = None
    transition_reason: Optional[str] = None
    battery_capacity_wh: Optional[float] = None
    solar_max_capacity_w: Optional[float] = None
    max_load_w: Optional[float] = None


class BackupPowerStateResponse(BackupPowerStateBase):
    id: int
    tenant_id: int
    event_id: Optional[int]
    battery_capacity_wh: Optional[float]
    solar_max_capacity_w: Optional[float]
    max_load_w: Optional[float]
    transition_timestamp: datetime
    transition_duration_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DataBackupSnapshotBase(BaseModel):
    snapshot_id: Optional[str] = None
    source: str
    record_count: Optional[int] = 0
    data_hash: str
    storage_uri: str
    status: Optional[str] = "created"
    integrity_verified: Optional[bool] = False
    verification_hash: Optional[str] = None
    verification_notes: Optional[str] = None
    verified_at: Optional[datetime] = None


class DataBackupSnapshotCreate(DataBackupSnapshotBase):
    event_id: Optional[int] = None


class DataBackupSnapshotVerifyRequest(BaseModel):
    verification_hash: Optional[str] = None
    verification_notes: Optional[str] = None
    status: Optional[str] = "verified"


class DataBackupSnapshotResponse(DataBackupSnapshotBase):
    id: int
    tenant_id: int
    event_id: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class DataSyncJobBase(BaseModel):
    sync_id: Optional[str] = None
    source_system: str
    target_system: str
    status: Optional[str] = "pending"
    attempt_count: Optional[int] = 0
    payload_hash: Optional[str] = None
    result_summary: Optional[str] = None
    last_attempt: Optional[datetime] = None


class DataSyncJobCreate(DataSyncJobBase):
    pass


class DataSyncJobResponse(DataSyncJobBase):
    id: int
    tenant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class DataSyncJobCompleteRequest(BaseModel):
    success: bool
    result_summary: Optional[str] = None
    payload_hash: Optional[str] = None


class RecoveryProcedureBase(BaseModel):
    procedure_name: str
    procedure_type: str
    description: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None


class RecoveryProcedureCreate(RecoveryProcedureBase):
    event_id: int


class EmergencyResponseCompleteRequest(BaseModel):
    success: bool
    error_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = {}


class RecoveryProcedureResponse(RecoveryProcedureBase):
    id: int
    event_id: int
    status: str
    total_steps: int
    completed_steps: int
    current_step: Optional[str]
    success: bool
    validation_passed: bool
    actual_duration_minutes: Optional[int]
    rollback_performed: bool
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True


class EmergencyStatusResponse(BaseModel):
    event_id: str
    event_type: str
    severity: str
    status: str
    response_count: int
    active_responses: List[str]
    backup_power_active: bool
    recovery_in_progress: bool
    estimated_recovery_time_minutes: Optional[int]
    affected_systems_count: int
    timestamp: datetime


class ManualOverrideRequest(BaseModel):
    action_type: str  # "fleet_stop", "safe_shutdown", "system_reset", "power_switch"
    reason: str
    target_systems: Optional[List[str]] = []
    force: bool = False  # Force override even if risky


class ManualOverrideResponse(BaseModel):
    override_id: str
    action_type: str
    status: str
    executed_at: datetime
    affected_count: int
    confirmation_required: bool
