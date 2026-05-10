# Aegis IoT Sensor Connector
# gRPC client for IoT sensor mesh communication
# Day 36: gRPC service definitions for IoT sensors

import asyncio
import logging
from typing import Dict, List, Optional, AsyncGenerator, Any
from datetime import datetime, timedelta
import grpc
import json

from ai.protos.sensors_pb2 import (
    SensorLocation, Coordinate3D, SensorHealth, SensorStatus,
    StreamMycelialDataRequest, MycelialData, MycelialStatus,
    StreamAcousticDataRequest, AcousticData, PestActivityStatus,
    SensorRegistration, SensorType, SensorCapabilities,
    GetZoneSensorsRequest, ZoneSensorsResponse, SensorNetworkHealth,
    BulkCalibrationRequest, CalibrationRequest, CalibrationType,
    EmergencyShutdownRequest, PestScanRequest
)
from ai.protos.sensors_pb2_grpc import (
    MycelialProbeServiceStub, AcousticPestMonitorServiceStub,
    SensorManagementServiceStub
)

logger = logging.getLogger(__name__)

class SensorConnector:
    """
    gRPC connector for IoT sensor mesh communication.
    Handles real-time data streaming from mycelial probes and acoustic monitors.
    """

    def __init__(self, host: str = "localhost", port: int = 50052):
        self.host = host
        self.port = port
        self.channel = None
        self.mycelial_stub = None
        self.acoustic_stub = None
        self.management_stub = None
        self.connected = False

    async def connect(self) -> bool:
        """Establish gRPC connection to sensor services."""
        try:
            self.channel = grpc.aio.insecure_channel(f"{self.host}:{self.port}")
            self.mycelial_stub = MycelialProbeServiceStub(self.channel)
            self.acoustic_stub = AcousticPestMonitorServiceStub(self.channel)
            self.management_stub = SensorManagementServiceStub(self.channel)

            # Test connection with a simple call
            await self.get_sensor_network_health()
            self.connected = True
            logger.info(f"Connected to sensor services at {self.host}:{self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to sensor services: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Close gRPC connection."""
        if self.channel:
            await self.channel.close()
            self.connected = False
            logger.info("Disconnected from sensor services")

    async def get_sensor_network_health(self) -> SensorNetworkHealth:
        """Get overall health status of the sensor network."""
        try:
            from google.protobuf.empty_pb2 import Empty
            response = await self.management_stub.GetSensorNetworkHealth(Empty())
            return response
        except Exception as e:
            logger.error(f"Failed to get sensor network health: {e}")
            # Return a basic health status for fallback
            return SensorNetworkHealth(
                total_sensors=0,
                active_sensors=0,
                offline_sensors=0,
                error_sensors=0,
                average_battery_level=0.0,
                network_uptime_percent=0.0,
                health_issues=[],
                report_timestamp=None
            )

    async def register_sensor(self, sensor_id: str, sensor_type: SensorType,
                            zone_id: int, position: tuple) -> bool:
        """Register a new sensor in the network."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            capabilities = SensorCapabilities(
                supported_data_types=["basic"],
                sampling_rate_hz=1.0,
                battery_capacity_mah=1000.0,
                supports_streaming=True,
                supports_calibration=True,
                communication_protocols=["grpc", "mqtt"]
            )

            registration = SensorRegistration(
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                location=location,
                capabilities=capabilities,
                firmware_version="1.0.0",
                installation_date=None
            )

            response = await self.management_stub.RegisterSensor(registration)
            logger.info(f"Registered sensor {sensor_id}: {response.registered}")
            return response.registered

        except Exception as e:
            logger.error(f"Failed to register sensor {sensor_id}: {e}")
            return False

    async def get_zone_sensors(self, zone_id: int,
                              sensor_types: List[int] = None) -> ZoneSensorsResponse:
        """Get all sensors in a specific zone."""
        try:
            request = GetZoneSensorsRequest(
                zone_id=zone_id,
                sensor_types=sensor_types or [],
                include_health_status=True
            )

            response = await self.management_stub.GetZoneSensors(request)
            return response

        except Exception as e:
            logger.error(f"Failed to get sensors for zone {zone_id}: {e}")
            return ZoneSensorsResponse(zone_id=zone_id, sensors=[], total_sensor_count=0)

    async def stream_mycelial_data(self, zone_id: int, position: tuple,
                                  data_types: List[str] = None) -> AsyncGenerator[MycelialData, None]:
        """Stream real-time mycelial probe data."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            # Convert string data types to enum values
            mycelial_data_types = []
            if data_types:
                from ai.protos.sensors_pb2 import MycelialDataType
                type_mapping = {
                    "biomass": MycelialDataType.MYCELIAL_BIOMASS,
                    "nutrients": MycelialDataType.NUTRIENT_TRANSPORT,
                    "water": MycelialDataType.WATER_CONTENT,
                    "ph": MycelialDataType.PH_LEVEL
                }
                mycelial_data_types = [type_mapping.get(dt, MycelialDataType.MYCELIAL_BIOMASS)
                                     for dt in data_types]

            request = StreamMycelialDataRequest(
                location=location,
                sampling_interval_ms=5000,  # 5 second intervals
                data_types=mycelial_data_types
            )

            async for data in self.mycelial_stub.StreamMycelialData(request):
                yield data

        except Exception as e:
            logger.error(f"Failed to stream mycelial data: {e}")
            return

    async def stream_acoustic_data(self, zone_id: int, position: tuple,
                                  sensitivity: float = 0.7) -> AsyncGenerator[AcousticData, None]:
        """Stream real-time acoustic pest monitoring data."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            request = StreamAcousticDataRequest(
                location=location,
                sampling_interval_ms=2000,  # 2 second intervals
                sensitivity_threshold=sensitivity,
                target_pests=[]  # All pests
            )

            async for data in self.acoustic_stub.StreamAcousticData(request):
                yield data

        except Exception as e:
            logger.error(f"Failed to stream acoustic data: {e}")
            return

    async def get_mycelial_status(self, zone_id: int, position: tuple) -> MycelialStatus:
        """Get current mycelial network status."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            status = await self.mycelial_stub.GetMycelialStatus(location)
            return status

        except Exception as e:
            logger.error(f"Failed to get mycelial status: {e}")
            return MycelialStatus(location=location, network_state=0)  # INACTIVE

    async def get_pest_activity_status(self, zone_id: int, position: tuple) -> PestActivityStatus:
        """Get current pest activity status."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            status = await self.acoustic_stub.GetPestActivityStatus(location)
            return status

        except Exception as e:
            logger.error(f"Failed to get pest activity status: {e}")
            return PestActivityStatus(location=location, pest_levels=[], alerts=[])

    async def trigger_pest_scan(self, zone_id: int, position: tuple,
                               duration_seconds: int = 60) -> bool:
        """Trigger an acoustic pest scan."""
        try:
            location = SensorLocation(
                zone_id=zone_id,
                position=Coordinate3D(x=position[0], y=position[1], z=position[2])
            )

            request = PestScanRequest(
                location=location,
                scan_duration_seconds=duration_seconds,
                target_pests=[],
                high_sensitivity=True
            )

            response = await self.acoustic_stub.TriggerPestScan(request)
            logger.info(f"Pest scan triggered: {response.scan_started}")
            return response.scan_started

        except Exception as e:
            logger.error(f"Failed to trigger pest scan: {e}")
            return False

    async def calibrate_sensor(self, sensor_id: str, calibration_type: int) -> bool:
        """Calibrate a specific sensor."""
        try:
            request = CalibrationRequest(
                sensor_id=sensor_id,
                calibration_type=calibration_type,
                calibration_parameters={}
            )

            # Try mycelial calibration first
            try:
                response = await self.mycelial_stub.CalibrateMycelialProbe(request)
                return response.calibration_started
            except:
                pass

            # Try acoustic calibration
            try:
                response = await self.acoustic_stub.CalibrateAcousticSensor(request)
                return response.calibration_started
            except:
                pass

            logger.warning(f"No calibration service available for sensor {sensor_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to calibrate sensor {sensor_id}: {e}")
            return False

    async def bulk_calibrate_sensors(self, sensor_ids: List[str],
                                    calibration_type: int) -> int:
        """Calibrate multiple sensors at once."""
        try:
            request = BulkCalibrationRequest(
                sensor_ids=sensor_ids,
                calibration_type=calibration_type,
                force_calibration=False
            )

            response = await self.management_stub.BulkCalibrateSensors(request)
            logger.info(f"Bulk calibration: {response.successfully_started}/{response.total_requested} started")
            return response.successfully_started

        except Exception as e:
            logger.error(f"Failed to bulk calibrate sensors: {e}")
            return 0

    async def emergency_shutdown(self, sensor_ids: List[str], reason: str) -> bool:
        """Emergency shutdown of sensors."""
        try:
            request = EmergencyShutdownRequest(
                sensor_ids=sensor_ids,
                reason=reason,
                immediate_shutdown=True
            )

            await self.management_stub.EmergencyShutdown(request)
            logger.warning(f"Emergency shutdown initiated for {len(sensor_ids)} sensors: {reason}")
            return True

        except Exception as e:
            logger.error(f"Failed to initiate emergency shutdown: {e}")
            return False

    async def get_sensor_health(self, sensor_id: str) -> SensorHealth:
        """Get health status of a specific sensor."""
        try:
            # Try to determine sensor type and location
            # This is a simplified implementation
            location = SensorLocation(zone_id=1, position=Coordinate3D(x=0, y=0, z=0))

            # Try mycelial health first
            try:
                health = await self.mycelial_stub.GetMycelialProbeHealth(location)
                return health
            except:
                pass

            # Try acoustic health
            try:
                health = await self.acoustic_stub.GetAcousticSensorHealth(location)
                return health
            except:
                pass

            # Return basic health status
            return SensorHealth(
                sensor_id=sensor_id,
                status=SensorStatus.SENSOR_OFFLINE,
                battery_level=0.0,
                signal_strength=0.0
            )

        except Exception as e:
            logger.error(f"Failed to get sensor health for {sensor_id}: {e}")
            return SensorHealth(sensor_id=sensor_id, status=SensorStatus.SENSOR_ERROR)

# Global sensor connector instance
sensor_connector: Optional[SensorConnector] = None

async def get_sensor_connector() -> SensorConnector:
    """Get or create the global sensor connector instance."""
    global sensor_connector
    if sensor_connector is None:
        sensor_connector = SensorConnector()
        await sensor_connector.connect()
    return sensor_connector

async def initialize_sensor_connector(host: str = "localhost", port: int = 50052) -> SensorConnector:
    """Initialize the sensor connector with specific host/port."""
    global sensor_connector
    sensor_connector = SensorConnector(host, port)
    await sensor_connector.connect()
    return sensor_connector