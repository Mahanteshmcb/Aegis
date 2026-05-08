# Aegis IoT Sensor Services Implementation
# gRPC server implementations for IoT sensor mesh
# Day 36: gRPC service definitions for IoT sensors

import asyncio
import logging
from typing import Dict, List, AsyncGenerator, Any
from datetime import datetime, timedelta
import random
import json

import grpc
from google.protobuf import timestamp_pb2, empty_pb2

from ai.protos.sensors_pb2 import (
    SensorLocation, Coordinate3D, SensorHealth, SensorStatus,
    StreamMycelialDataRequest, MycelialData, MycelialStatus, MycelialReading,
    MycelialDataType, MycelialNetworkState, MycelialAlert, MycelialAlertType,
    StreamAcousticDataRequest, AcousticData, AcousticDetection, PestType,
    AcousticEnvironment, PestActivityStatus, PestActivityLevel, PestAlert,
    SensorRegistration, SensorType, SensorCapabilities, SensorRegistrationResponse,
    GetZoneSensorsRequest, ZoneSensorsResponse, SensorInfo, SensorNetworkHealth,
    SensorHealthIssue, BulkCalibrationRequest, BulkCalibrationResponse,
    CalibrationResult, EmergencyShutdownRequest, CalibrationRequest,
    CalibrationResponse, CalibrationType, PestScanRequest, PestScanResponse,
    AlertSeverity, ActivityLevel
)
from ai.protos.sensors_pb2_grpc import (
    MycelialProbeServiceServicer, AcousticPestMonitorServiceServicer,
    SensorManagementServiceServicer, add_MycelialProbeServiceServicer_to_server,
    add_AcousticPestMonitorServiceServicer_to_server,
    add_SensorManagementServiceServicer_to_server
)

logger = logging.getLogger(__name__)

class MockMycelialProbeService(MycelialProbeServiceServicer):
    """Mock implementation of mycelial probe service for testing."""

    def __init__(self):
        self.active_sensors: Dict[str, Dict] = {}
        self.mycelial_data_history: Dict[str, List] = {}

    async def StreamMycelialData(self, request: StreamMycelialDataRequest,
                                context) -> AsyncGenerator[MycelialData, None]:
        """Stream real-time mycelial data."""
        sensor_id = f"myco_{request.location.zone_id}_{request.location.position.x}_{request.location.position.y}"

        logger.info(f"Starting mycelial data stream for sensor {sensor_id}")

        try:
            while not context.is_active():
                await asyncio.sleep(request.sampling_interval_ms / 1000.0)

                # Generate mock mycelial readings
                readings = []
                data_types = request.data_types or [MycelialDataType.MYCELIAL_BIOMASS,
                                                   MycelialDataType.NUTRIENT_TRANSPORT,
                                                   MycelialDataType.WATER_CONTENT]

                for data_type in data_types:
                    value = self._generate_mycelial_reading(data_type)
                    reading = MycelialReading(
                        data_type=data_type,
                        value=value,
                        unit=self._get_unit_for_data_type(data_type),
                        confidence=random.uniform(0.8, 0.95)
                    )
                    readings.append(reading)

                # Create health status
                health = SensorHealth(
                    sensor_id=sensor_id,
                    status=SensorStatus.SENSOR_ACTIVE,
                    battery_level=random.uniform(0.7, 0.9),
                    signal_strength=random.uniform(0.8, 1.0),
                    last_reading=timestamp_pb2.Timestamp()
                )
                health.last_reading.FromDatetime(datetime.now())

                data = MycelialData(
                    sensor_id=sensor_id,
                    location=request.location,
                    timestamp=timestamp_pb2.Timestamp(),
                    readings=readings,
                    health=health
                )
                data.timestamp.FromDatetime(datetime.now())

                yield data

        except Exception as e:
            logger.error(f"Error in mycelial data stream: {e}")

    async def GetMycelialStatus(self, request: SensorLocation, context) -> MycelialStatus:
        """Get current mycelial network status."""
        # Generate mock status
        biomass_density = random.uniform(0.3, 0.8)
        network_state = MycelialNetworkState.MYCELIAL_ACTIVE

        # Generate occasional alerts
        alerts = []
        if random.random() < 0.1:  # 10% chance of alert
            alert_types = [MycelialAlertType.BIOMASS_LOW, MycelialAlertType.NUTRIENT_BLOCKAGE,
                          MycelialAlertType.WATER_STRESS]
            alert_type = random.choice(alert_types)

            alert = MycelialAlert(
                alert_type=alert_type,
                message=f"Mycelial {alert_type.name.lower().replace('_', ' ')} detected",
                severity=AlertSeverity.MEDIUM,
                timestamp=timestamp_pb2.Timestamp()
            )
            alert.timestamp.FromDatetime(datetime.now())
            alerts.append(alert)

        status = MycelialStatus(
            location=request,
            network_state=network_state,
            biomass_density=biomass_density,
            alerts=alerts,
            last_update=timestamp_pb2.Timestamp()
        )
        status.last_update.FromDatetime(datetime.now())

        return status

    async def CalibrateMycelialProbe(self, request: CalibrationRequest, context) -> CalibrationResponse:
        """Calibrate mycelial probe sensor."""
        logger.info(f"Calibrating mycelial probe {request.sensor_id}")

        response = CalibrationResponse(
            calibration_started=True,
            calibration_id=f"cal_{request.sensor_id}_{datetime.now().timestamp()}",
            estimated_duration_seconds=300,  # 5 minutes
            calibration_steps=[
                "Initializing calibration sequence",
                "Measuring baseline readings",
                "Adjusting sensor sensitivity",
                "Verifying calibration accuracy"
            ]
        )

        return response

    async def GetMycelialProbeHealth(self, request: SensorLocation, context) -> SensorHealth:
        """Get mycelial probe health status."""
        sensor_id = f"myco_{request.zone_id}_{request.position.x}_{request.position.y}"

        health = SensorHealth(
            sensor_id=sensor_id,
            status=SensorStatus.SENSOR_ACTIVE,
            battery_level=random.uniform(0.6, 0.9),
            signal_strength=random.uniform(0.7, 1.0),
            last_calibration=timestamp_pb2.Timestamp(),
            last_reading=timestamp_pb2.Timestamp()
        )

        health.last_calibration.FromDatetime(datetime.now() - timedelta(hours=random.randint(1, 24)))
        health.last_reading.FromDatetime(datetime.now() - timedelta(minutes=random.randint(1, 60)))

        return health

    def _generate_mycelial_reading(self, data_type: MycelialDataType) -> float:
        """Generate mock mycelial reading based on data type."""
        ranges = {
            MycelialDataType.MYCELIAL_BIOMASS: (0.1, 1.0),
            MycelialDataType.NUTRIENT_TRANSPORT: (0.0, 100.0),
            MycelialDataType.WATER_CONTENT: (0.2, 0.9),
            MycelialDataType.PH_LEVEL: (5.5, 7.5),
            MycelialDataType.ELECTRICAL_ACTIVITY: (0.1, 5.0),
            MycelialDataType.SPORE_CONCENTRATION: (10, 1000),
            MycelialDataType.ROOT_COLONIZATION: (0.0, 1.0),
            MycelialDataType.DECOMPOSITION_RATE: (0.01, 0.1)
        }

        min_val, max_val = ranges.get(data_type, (0.0, 1.0))
        return random.uniform(min_val, max_val)

    def _get_unit_for_data_type(self, data_type: MycelialDataType) -> str:
        """Get unit string for data type."""
        units = {
            MycelialDataType.MYCELIAL_BIOMASS: "g/cm³",
            MycelialDataType.NUTRIENT_TRANSPORT: "μg/min",
            MycelialDataType.WATER_CONTENT: "%",
            MycelialDataType.PH_LEVEL: "pH",
            MycelialDataType.ELECTRICAL_ACTIVITY: "μV",
            MycelialDataType.SPORE_CONCENTRATION: "spores/m³",
            MycelialDataType.ROOT_COLONIZATION: "ratio",
            MycelialDataType.DECOMPOSITION_RATE: "g/day"
        }
        return units.get(data_type, "unit")


class MockAcousticPestMonitorService(AcousticPestMonitorServiceServicer):
    """Mock implementation of acoustic pest monitor service for testing."""

    def __init__(self):
        self.active_scans: Dict[str, Dict] = {}

    async def StreamAcousticData(self, request: StreamAcousticDataRequest,
                                context) -> AsyncGenerator[AcousticData, None]:
        """Stream real-time acoustic pest detection data."""
        sensor_id = f"acoustic_{request.location.zone_id}_{request.location.position.x}_{request.location.position.y}"

        logger.info(f"Starting acoustic data stream for sensor {sensor_id}")

        try:
            while not context.is_active():
                await asyncio.sleep(request.sampling_interval_ms / 1000.0)

                # Generate mock acoustic detections
                detections = []
                if random.random() < 0.3:  # 30% chance of detection
                    pest_type = random.choice(list(PestType))
                    if pest_type != PestType.UNKNOWN:
                        detection = AcousticDetection(
                            pest_type=pest_type,
                            confidence_score=random.uniform(0.6, 0.95),
                            frequency_hz=random.uniform(20, 2000),
                            amplitude=random.uniform(0.1, 1.0),
                            estimated_location=Coordinate3D(
                                x=request.location.position.x + random.uniform(-2, 2),
                                y=request.location.position.y + random.uniform(-2, 2),
                                z=request.location.position.z
                            ),
                            detection_time=timestamp_pb2.Timestamp()
                        )
                        detection.detection_time.FromDatetime(datetime.now())
                        detections.append(detection)

                # Create environment data
                environment = AcousticEnvironment(
                    background_noise_level=random.uniform(20, 40),
                    wind_speed_ms=random.uniform(0, 5),
                    temperature_c=random.uniform(15, 30),
                    humidity_percent=random.uniform(40, 80),
                    weather_conditions="clear"
                )

                # Create health status
                health = SensorHealth(
                    sensor_id=sensor_id,
                    status=SensorStatus.SENSOR_ACTIVE,
                    battery_level=random.uniform(0.7, 0.9),
                    signal_strength=random.uniform(0.8, 1.0),
                    last_reading=timestamp_pb2.Timestamp()
                )
                health.last_reading.FromDatetime(datetime.now())

                data = AcousticData(
                    sensor_id=sensor_id,
                    location=request.location,
                    timestamp=timestamp_pb2.Timestamp(),
                    detections=detections,
                    environment=environment,
                    health=health
                )
                data.timestamp.FromDatetime(datetime.now())

                yield data

        except Exception as e:
            logger.error(f"Error in acoustic data stream: {e}")

    async def GetPestActivityStatus(self, request: SensorLocation, context) -> PestActivityStatus:
        """Get current pest activity status."""
        # Generate mock pest activity levels
        pest_levels = []
        pest_types = [PestType.APHID, PestType.BEETLE, PestType.CATERPILLAR]

        for pest_type in pest_types:
            level = ActivityLevel(random.randint(0, 3))  # NONE to HIGH
            pest_level = PestActivityLevel(
                pest_type=pest_type,
                level=level,
                trend_direction=random.uniform(-0.5, 0.5),
                last_detection=timestamp_pb2.Timestamp()
            )
            pest_level.last_detection.FromDatetime(
                datetime.now() - timedelta(hours=random.randint(1, 24))
            )
            pest_levels.append(pest_level)

        # Generate occasional alerts
        alerts = []
        if random.random() < 0.15:  # 15% chance of alert
            alert = PestAlert(
                pest_type=random.choice(pest_types),
                message="Elevated pest activity detected",
                severity=AlertSeverity.HIGH,
                location=Coordinate3D(x=request.position.x, y=request.position.y, z=request.position.z),
                timestamp=timestamp_pb2.Timestamp()
            )
            alert.timestamp.FromDatetime(datetime.now())
            alerts.append(alert)

        environment = AcousticEnvironment(
            background_noise_level=random.uniform(25, 35),
            wind_speed_ms=random.uniform(0, 3),
            temperature_c=random.uniform(18, 25),
            humidity_percent=random.uniform(50, 70),
            weather_conditions="moderate"
        )

        status = PestActivityStatus(
            location=request,
            pest_levels=pest_levels,
            environment=environment,
            alerts=alerts,
            last_scan=timestamp_pb2.Timestamp()
        )
        status.last_scan.FromDatetime(datetime.now() - timedelta(minutes=random.randint(10, 120)))

        return status

    async def TriggerPestScan(self, request: PestScanRequest, context) -> PestScanResponse:
        """Trigger an acoustic pest scan."""
        scan_id = f"scan_{request.location.zone_id}_{datetime.now().timestamp()}"

        logger.info(f"Triggering pest scan {scan_id} for zone {request.location.zone_id}")

        response = PestScanResponse(
            scan_started=True,
            scan_id=scan_id,
            estimated_duration_seconds=request.scan_duration_seconds,
            target_frequencies=["20-200Hz", "200-2000Hz", "2-20kHz"]
        )

        return response

    async def CalibrateAcousticSensor(self, request: CalibrationRequest, context) -> CalibrationResponse:
        """Calibrate acoustic sensor."""
        logger.info(f"Calibrating acoustic sensor {request.sensor_id}")

        response = CalibrationResponse(
            calibration_started=True,
            calibration_id=f"cal_{request.sensor_id}_{datetime.now().timestamp()}",
            estimated_duration_seconds=180,  # 3 minutes
            calibration_steps=[
                "Measuring ambient noise levels",
                "Calibrating frequency response",
                "Testing sensitivity thresholds",
                "Verifying detection accuracy"
            ]
        )

        return response

    async def GetAcousticSensorHealth(self, request: SensorLocation, context) -> SensorHealth:
        """Get acoustic sensor health status."""
        sensor_id = f"acoustic_{request.zone_id}_{request.position.x}_{request.position.y}"

        health = SensorHealth(
            sensor_id=sensor_id,
            status=SensorStatus.SENSOR_ACTIVE,
            battery_level=random.uniform(0.6, 0.9),
            signal_strength=random.uniform(0.7, 1.0),
            last_calibration=timestamp_pb2.Timestamp(),
            last_reading=timestamp_pb2.Timestamp()
        )

        health.last_calibration.FromDatetime(datetime.now() - timedelta(hours=random.randint(1, 24)))
        health.last_reading.FromDatetime(datetime.now() - timedelta(minutes=random.randint(1, 60)))

        return health


class MockSensorManagementService(SensorManagementServiceServicer):
    """Mock implementation of sensor management service for testing."""

    def __init__(self):
        self.registered_sensors: Dict[str, SensorInfo] = {}
        self.network_health = SensorNetworkHealth(
            total_sensors=0,
            active_sensors=0,
            offline_sensors=0,
            error_sensors=0,
            average_battery_level=0.8,
            network_uptime_percent=95.0,
            health_issues=[],
            report_timestamp=timestamp_pb2.Timestamp()
        )

    async def RegisterSensor(self, request: SensorRegistration, context) -> SensorRegistrationResponse:
        """Register a new sensor in the network."""
        logger.info(f"Registering sensor {request.sensor_id} of type {request.sensor_type}")

        # Create sensor info
        sensor_info = SensorInfo(
            sensor_id=request.sensor_id,
            sensor_type=request.sensor_type,
            location=request.location,
            health=SensorHealth(
                sensor_id=request.sensor_id,
                status=SensorStatus.SENSOR_ACTIVE,
                battery_level=1.0,
                signal_strength=1.0,
                last_calibration=timestamp_pb2.Timestamp(),
                last_reading=timestamp_pb2.Timestamp()
            ),
            capabilities=request.capabilities,
            last_communication=timestamp_pb2.Timestamp()
        )

        sensor_info.health.last_calibration.FromDatetime(datetime.now())
        sensor_info.health.last_reading.FromDatetime(datetime.now())
        sensor_info.last_communication.FromDatetime(datetime.now())

        self.registered_sensors[request.sensor_id] = sensor_info
        self.network_health.total_sensors += 1
        self.network_health.active_sensors += 1

        response = SensorRegistrationResponse(
            registered=True,
            assigned_network_id=f"net_{request.sensor_id}",
            initial_health=sensor_info.health,
            configuration_instructions=[
                "Sensor registered successfully",
                "Calibration recommended within 24 hours",
                "Monitor battery levels regularly"
            ]
        )

        return response

    async def GetZoneSensors(self, request: GetZoneSensorsRequest, context) -> ZoneSensorsResponse:
        """Get all sensors in a zone."""
        zone_sensors = [
            sensor for sensor in self.registered_sensors.values()
            if sensor.location.zone_id == request.zone_id and
            (not request.sensor_types or sensor.sensor_type in request.sensor_types)
        ]

        response = ZoneSensorsResponse(
            zone_id=request.zone_id,
            sensors=zone_sensors,
            total_sensor_count=len(zone_sensors),
            last_updated=timestamp_pb2.Timestamp()
        )
        response.last_updated.FromDatetime(datetime.now())

        return response

    async def GetSensorNetworkHealth(self, request: empty_pb2.Empty, context) -> SensorNetworkHealth:
        """Get overall sensor network health."""
        # Update health metrics
        self.network_health.report_timestamp.FromDatetime(datetime.now())

        # Generate some mock health issues occasionally
        if random.random() < 0.1:  # 10% chance
            issue = SensorHealthIssue(
                sensor_id="mock_sensor_001",
                issue_type="Low Battery",
                severity=AlertSeverity.MEDIUM,
                description="Battery level below 20%",
                detected_at=timestamp_pb2.Timestamp()
            )
            issue.detected_at.FromDatetime(datetime.now())
            self.network_health.health_issues.append(issue)

        return self.network_health

    async def BulkCalibrateSensors(self, request: BulkCalibrationRequest, context) -> BulkCalibrationResponse:
        """Bulk calibrate multiple sensors."""
        logger.info(f"Bulk calibrating {len(request.sensor_ids)} sensors")

        results = []
        successful_count = 0

        for sensor_id in request.sensor_ids:
            result = CalibrationResult(
                sensor_id=sensor_id,
                calibration_started=random.random() > 0.1,  # 90% success rate
                status_message="Calibration initiated" if random.random() > 0.1 else "Sensor offline",
                estimated_completion=timestamp_pb2.Timestamp()
            )
            result.estimated_completion.FromDatetime(datetime.now() + timedelta(minutes=5))

            results.append(result)
            if result.calibration_started:
                successful_count += 1

        response = BulkCalibrationResponse(
            total_requested=len(request.sensor_ids),
            successfully_started=successful_count,
            results=results
        )

        return response

    async def EmergencyShutdown(self, request: EmergencyShutdownRequest, context) -> empty_pb2.Empty:
        """Emergency shutdown of sensors."""
        logger.warning(f"Emergency shutdown requested for {len(request.sensor_ids)} sensors: {request.reason}")

        # In a real implementation, this would trigger emergency protocols
        # For mock, just log and return

        return empty_pb2.Empty()


async def serve_sensor_services(host: str = "localhost", port: int = 50052):
    """Start the sensor services gRPC server."""
    server = grpc.aio.server()

    # Add services
    mycelial_service = MockMycelialProbeService()
    acoustic_service = MockAcousticPestMonitorService()
    management_service = MockSensorManagementService()

    add_MycelialProbeServiceServicer_to_server(mycelial_service, server)
    add_AcousticPestMonitorServiceServicer_to_server(acoustic_service, server)
    add_SensorManagementServiceServicer_to_server(management_service, server)

    # Start server
    server.add_insecure_port(f"{host}:{port}")
    await server.start()

    logger.info(f"Aegis IoT Sensor Services started on {host}:{port}")
    logger.info("Available services:")
    logger.info("  - MycelialProbeService")
    logger.info("  - AcousticPestMonitorService")
    logger.info("  - SensorManagementService")

    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down sensor services...")
        await server.stop(5)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve_sensor_services())