# Backend Router for IoT Sensor Services
# REST API endpoints for sensor management and monitoring
# Day 36: gRPC service definitions for IoT sensors

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ai.sensor_connector import get_sensor_connector, SensorConnector
from ai.protos.sensors_pb2 import SensorType, CalibrationType

router = APIRouter(prefix="/api/v1/iot-sensors", tags=["iot-sensors"])
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class SensorRegistrationRequest(BaseModel):
    sensor_id: str
    sensor_type: str  # Will be converted to SensorType enum
    zone_id: int
    position: Dict[str, float]  # {"x": float, "y": float, "z": float}

class SensorInfoResponse(BaseModel):
    sensor_id: str
    sensor_type: str
    zone_id: int
    position: Dict[str, float]
    status: str
    battery_level: float
    signal_strength: float
    last_reading: Optional[datetime]
    capabilities: Dict[str, Any]

class SensorNetworkHealthResponse(BaseModel):
    total_sensors: int
    active_sensors: int
    offline_sensors: int
    error_sensors: int
    average_battery_level: float
    network_uptime_percent: float
    health_issues: List[Dict[str, Any]]
    report_timestamp: datetime

class MycelialDataResponse(BaseModel):
    sensor_id: str
    zone_id: int
    position: Dict[str, float]
    timestamp: datetime
    readings: List[Dict[str, Any]]
    health: Dict[str, Any]

class AcousticDataResponse(BaseModel):
    sensor_id: str
    zone_id: int
    position: Dict[str, float]
    timestamp: datetime
    detections: List[Dict[str, Any]]
    environment: Dict[str, Any]
    health: Dict[str, Any]

class PestActivityResponse(BaseModel):
    zone_id: int
    position: Dict[str, float]
    pest_levels: List[Dict[str, Any]]
    alerts: List[Dict[str, Any]]
    environment: Dict[str, Any]
    last_scan: Optional[datetime]

class CalibrationRequestModel(BaseModel):
    sensor_ids: List[str]
    calibration_type: str = "STANDARD_CALIBRATION"

class BulkOperationResponse(BaseModel):
    total_requested: int
    successful_operations: int
    failed_operations: int
    results: List[Dict[str, Any]]

# Dependency to get sensor connector
async def get_sensor_conn() -> SensorConnector:
    """Dependency to get the sensor connector instance."""
    return await get_sensor_connector()

@router.post("/register", summary="Register New IoT Sensor")
async def register_sensor(request: SensorRegistrationRequest,
                         sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Register a new IoT sensor in the sensor network.

    This endpoint registers specialized sensors like mycelial probes and acoustic monitors
    with the IoT sensor management service.
    """
    try:
        # Convert string sensor type to enum
        sensor_type_map = {
            "mycelial_probe": SensorType.MYCELIAL_PROBE,
            "acoustic_monitor": SensorType.ACOUSTIC_MONITOR,
            "soil_moisture": SensorType.SOIL_MOISTURE,
            "nutrient_analyzer": SensorType.NUTRIENT_ANALYZER,
            "weather_station": SensorType.WEATHER_STATION,
            "visual_camera": SensorType.VISUAL_CAMERA,
            "thermal_imager": SensorType.THERMAL_IMAGER,
            "gas_analyzer": SensorType.GAS_ANALYZER
        }

        sensor_type = sensor_type_map.get(request.sensor_type.lower())
        if not sensor_type:
            raise HTTPException(status_code=400, detail=f"Invalid sensor type: {request.sensor_type}")

        position = (request.position["x"], request.position["y"], request.position.get("z", 0.0))

        success = await sensor_conn.register_sensor(
            request.sensor_id,
            sensor_type,
            request.zone_id,
            position
        )

        if success:
            return {
                "message": f"IoT Sensor {request.sensor_id} registered successfully",
                "sensor_id": request.sensor_id,
                "sensor_type": request.sensor_type,
                "zone_id": request.zone_id,
                "status": "registered"
            }
        else:
            raise HTTPException(status_code=500, detail="Sensor registration failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register IoT sensor: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.get("/network/health", summary="Get IoT Sensor Network Health")
async def get_network_health(sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Get comprehensive health status of the IoT sensor network.

    Returns metrics on sensor connectivity, battery levels, and network issues
    for specialized IoT sensors (mycelial probes, acoustic monitors, etc.).
    """
    try:
        health = await sensor_conn.get_sensor_network_health()

        return SensorNetworkHealthResponse(
            total_sensors=health.total_sensors,
            active_sensors=health.active_sensors,
            offline_sensors=health.offline_sensors,
            error_sensors=health.error_sensors,
            average_battery_level=health.average_battery_level,
            network_uptime_percent=health.network_uptime_percent,
            health_issues=[
                {
                    "sensor_id": issue.sensor_id,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description,
                    "detected_at": issue.detected_at.ToDatetime() if issue.detected_at else None
                }
                for issue in health.health_issues
            ],
            report_timestamp=health.report_timestamp.ToDatetime() if health.report_timestamp else datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to get IoT network health: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/zone/{zone_id}", summary="Get Zone IoT Sensors")
async def get_zone_sensors(zone_id: int, sensor_type: Optional[str] = None,
                          sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Get all IoT sensors deployed in a specific zone.

    Optionally filter by sensor type (mycelial_probe, acoustic_monitor, etc.).
    """
    try:
        sensor_types = []
        if sensor_type:
            sensor_type_map = {
                "mycelial_probe": SensorType.MYCELIAL_PROBE,
                "acoustic_monitor": SensorType.ACOUSTIC_MONITOR,
                "soil_moisture": SensorType.SOIL_MOISTURE,
                "nutrient_analyzer": SensorType.NUTRIENT_ANALYZER,
                "weather_station": SensorType.WEATHER_STATION,
                "visual_camera": SensorType.VISUAL_CAMERA,
                "thermal_imager": SensorType.THERMAL_IMAGER,
                "gas_analyzer": SensorType.GAS_ANALYZER
            }
            sensor_enum = sensor_type_map.get(sensor_type.lower())
            if sensor_enum:
                sensor_types = [sensor_enum]

        zone_response = await sensor_conn.get_zone_sensors(zone_id, sensor_types)

        sensors = []
        for sensor in zone_response.sensors:
            sensor_info = SensorInfoResponse(
                sensor_id=sensor.sensor_id,
                sensor_type=sensor.sensor_type,
                zone_id=sensor.location.zone_id,
                position={
                    "x": sensor.location.position.x,
                    "y": sensor.location.position.y,
                    "z": sensor.location.position.z
                },
                status=sensor.health.status,
                battery_level=sensor.health.battery_level,
                signal_strength=sensor.health.signal_strength,
                last_reading=sensor.health.last_reading.ToDatetime() if sensor.health.last_reading else None,
                capabilities={
                    "supported_data_types": list(sensor.capabilities.supported_data_types),
                    "sampling_rate_hz": sensor.capabilities.sampling_rate_hz,
                    "battery_capacity_mah": sensor.capabilities.battery_capacity_mah,
                    "supports_streaming": sensor.capabilities.supports_streaming,
                    "supports_calibration": sensor.capabilities.supports_calibration,
                    "communication_protocols": list(sensor.capabilities.communication_protocols)
                }
            )
            sensors.append(sensor_info)

        return {
            "zone_id": zone_id,
            "total_sensors": zone_response.total_sensor_count,
            "sensors": sensors,
            "last_updated": zone_response.last_updated.ToDatetime() if zone_response.last_updated else datetime.now()
        }

    except Exception as e:
        logger.error(f"Failed to get zone IoT sensors: {e}")
        raise HTTPException(status_code=500, detail=f"Zone sensors retrieval failed: {str(e)}")

@router.get("/mycelial/status/{zone_id}", summary="Get Mycelial Network Status")
async def get_mycelial_status(zone_id: int, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                             sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Get current status of mycelial network in a zone.

    Returns biomass density, network state, and any alerts from sub-surface mycelial probes.
    """
    try:
        position = (x, y, z)
        status = await sensor_conn.get_mycelial_status(zone_id, position)

        return {
            "zone_id": zone_id,
            "position": {"x": x, "y": y, "z": z},
            "network_state": status.network_state,
            "biomass_density": status.biomass_density,
            "alerts": [
                {
                    "alert_type": alert.alert_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "timestamp": alert.timestamp.ToDatetime() if alert.timestamp else None
                }
                for alert in status.alerts
            ],
            "last_update": status.last_update.ToDatetime() if status.last_update else None
        }

    except Exception as e:
        logger.error(f"Failed to get mycelial status: {e}")
        raise HTTPException(status_code=500, detail=f"Mycelial status retrieval failed: {str(e)}")

@router.get("/pest/activity/{zone_id}", summary="Get Pest Activity Status")
async def get_pest_activity(zone_id: int, x: float = 0.0, y: float = 0.0, z: float = 0.0,
                           sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Get current pest activity levels in a zone from acoustic pest monitors.

    Returns pest monitoring data and any active alerts.
    """
    try:
        position = (x, y, z)
        status = await sensor_conn.get_pest_activity_status(zone_id, position)

        return PestActivityResponse(
            zone_id=zone_id,
            position={"x": x, "y": y, "z": z},
            pest_levels=[
                {
                    "pest_type": level.pest_type,
                    "activity_level": level.level,
                    "trend_direction": level.trend_direction,
                    "last_detection": level.last_detection.ToDatetime() if level.last_detection else None
                }
                for level in status.pest_levels
            ],
            alerts=[
                {
                    "pest_type": alert.pest_type,
                    "message": alert.message,
                    "severity": alert.severity,
                    "location": {"x": alert.location.x, "y": alert.location.y, "z": alert.location.z},
                    "timestamp": alert.timestamp.ToDatetime() if alert.timestamp else None
                }
                for alert in status.alerts
            ],
            environment={
                "background_noise_level": status.environment.background_noise_level,
                "wind_speed_ms": status.environment.wind_speed_ms,
                "temperature_c": status.environment.temperature_c,
                "humidity_percent": status.environment.humidity_percent,
                "weather_conditions": status.environment.weather_conditions
            },
            last_scan=status.last_scan.ToDatetime() if status.last_scan else None
        )

    except Exception as e:
        logger.error(f"Failed to get pest activity: {e}")
        raise HTTPException(status_code=500, detail=f"Pest activity retrieval failed: {str(e)}")

@router.post("/pest/scan/{zone_id}", summary="Trigger Acoustic Pest Scan")
async def trigger_pest_scan(zone_id: int, duration_seconds: int = 60,
                           x: float = 0.0, y: float = 0.0, z: float = 0.0,
                           sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Trigger an intensive acoustic pest scan in a zone.

    Initiates high-sensitivity pest monitoring for the specified duration using acoustic sensors.
    """
    try:
        position = (x, y, z)
        success = await sensor_conn.trigger_pest_scan(zone_id, position, duration_seconds)

        if success:
            return {
                "message": f"Acoustic pest scan initiated for zone {zone_id}",
                "zone_id": zone_id,
                "position": {"x": x, "y": y, "z": z},
                "duration_seconds": duration_seconds,
                "status": "scan_started"
            }
        else:
            raise HTTPException(status_code=500, detail="Pest scan failed to start")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger pest scan: {e}")
        raise HTTPException(status_code=500, detail=f"Pest scan failed: {str(e)}")

@router.post("/calibrate", summary="Calibrate IoT Sensors")
async def calibrate_sensors(request: CalibrationRequestModel,
                           sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Calibrate one or more IoT sensors.

    Supports standard calibration, factory reset, and field calibration for specialized sensors.
    """
    try:
        calibration_type_map = {
            "standard_calibration": CalibrationType.STANDARD_CALIBRATION,
            "factory_reset": CalibrationType.FACTORY_RESET,
            "field_calibration": CalibrationType.FIELD_CALIBRATION,
            "temperature_compensation": CalibrationType.TEMPERATURE_COMPENSATION
        }

        calibration_type = calibration_type_map.get(request.calibration_type.lower(),
                                                   CalibrationType.STANDARD_CALIBRATION)

        if len(request.sensor_ids) == 1:
            # Single sensor calibration
            success = await sensor_conn.calibrate_sensor(request.sensor_ids[0], calibration_type)
            successful_count = 1 if success else 0
        else:
            # Bulk calibration
            successful_count = await sensor_conn.bulk_calibrate_sensors(request.sensor_ids, calibration_type)

        return BulkOperationResponse(
            total_requested=len(request.sensor_ids),
            successful_operations=successful_count,
            failed_operations=len(request.sensor_ids) - successful_count,
            results=[
                {
                    "sensor_id": sensor_id,
                    "success": True,  # Simplified - would need actual results
                    "message": "Calibration initiated"
                }
                for sensor_id in request.sensor_ids
            ]
        )

    except Exception as e:
        logger.error(f"Failed to calibrate IoT sensors: {e}")
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")

@router.post("/emergency/shutdown", summary="Emergency IoT Sensor Shutdown")
async def emergency_shutdown(sensor_ids: List[str], reason: str = "System emergency",
                            sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Emergency shutdown of specified IoT sensors.

    Use only in critical situations requiring immediate shutdown of specialized sensors.
    """
    try:
        success = await sensor_conn.emergency_shutdown(sensor_ids, reason)

        if success:
            return {
                "message": f"Emergency shutdown initiated for {len(sensor_ids)} IoT sensors",
                "sensor_ids": sensor_ids,
                "reason": reason,
                "timestamp": datetime.now(),
                "status": "shutdown_initiated"
            }
        else:
            raise HTTPException(status_code=500, detail="Emergency shutdown failed")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate emergency shutdown: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency shutdown failed: {str(e)}")

@router.post("/stream/mycelial/{zone_id}", summary="Start Mycelial Data Streaming")
async def stream_mycelial_data(zone_id: int, background_tasks: BackgroundTasks,
                              x: float = 0.0, y: float = 0.0, z: float = 0.0,
                              sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Start streaming real-time mycelial probe data to the orchestration engine.

    This initiates background data collection from sub-surface mycelial sensors
    for integration with the Succession & Orchestration engine.
    """
    try:
        position = (x, y, z)

        # Start streaming in background
        background_tasks.add_task(
            sensor_conn.stream_mycelial_data,
            zone_id,
            position
        )

        return {
            "message": f"Mycelial data streaming started for zone {zone_id}",
            "zone_id": zone_id,
            "position": {"x": x, "y": y, "z": z},
            "status": "streaming_started",
            "note": "Data is being streamed to the orchestration engine for real-time processing"
        }

    except Exception as e:
        logger.error(f"Failed to start mycelial streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

@router.post("/stream/acoustic/{zone_id}", summary="Start Acoustic Data Streaming")
async def stream_acoustic_data(zone_id: int, background_tasks: BackgroundTasks,
                              x: float = 0.0, y: float = 0.0, z: float = 0.0,
                              sensor_conn: SensorConnector = Depends(get_sensor_conn)):
    """
    Start streaming real-time acoustic pest monitoring data to the orchestration engine.

    This initiates background data collection from acoustic sensors
    for integration with the Succession & Orchestration engine.
    """
    try:
        position = (x, y, z)

        # Start streaming in background
        background_tasks.add_task(
            sensor_conn.stream_acoustic_data,
            zone_id,
            position
        )

        return {
            "message": f"Acoustic data streaming started for zone {zone_id}",
            "zone_id": zone_id,
            "position": {"x": x, "y": y, "z": z},
            "status": "streaming_started",
            "note": "Data is being streamed to the orchestration engine for real-time pest detection"
        }

    except Exception as e:
        logger.error(f"Failed to start acoustic streaming: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")