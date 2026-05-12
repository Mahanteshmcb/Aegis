# Day 37: Integration testing for gRPC contracts
# Comprehensive end-to-end testing of gRPC communication flows

import pytest
import asyncio
import time
import threading
import grpc
from concurrent import futures
from typing import Dict, List, Any
import logging

from ai.mock_clients import (
    MockMycelialProbe, MockAcousticPestMonitor, SensorSimulatorManager,
    MockAegisRover, MockAgriSwarmBot, MockCanopyDrone, RoboticFleetManager
)
from ai.sensor_services import (
    MockMycelialProbeService, MockAcousticPestMonitorService,
    MockSensorManagementService
)
from ai.protos.sensors_pb2 import (
    SensorLocation, Coordinate3D, SensorHealth, SensorStatus,
    StreamMycelialDataRequest, StreamAcousticDataRequest,
    SensorRegistration, SensorType, SensorCapabilities,
    GetZoneSensorsRequest, ZoneSensorsResponse,
    SensorNetworkHealth, SensorHealthIssue,
    BulkCalibrationRequest, BulkCalibrationResponse,
    CalibrationType, EmergencyShutdownRequest, PestType,
    AcousticEnvironment, MycelialDataType
)
from ai.protos.sensors_pb2_grpc import (
    MycelialProbeServiceStub, AcousticPestMonitorServiceStub,
    SensorManagementServiceStub, add_MycelialProbeServiceServicer_to_server,
    add_AcousticPestMonitorServiceServicer_to_server,
    add_SensorManagementServiceServicer_to_server
)
from google.protobuf import empty_pb2
from ai.protos.robotics_pb2 import (
    RoboticCommand, CommandType, NavigationCommand, HarvestCommand,
    MaintenanceCommand, RoboticStatus, FleetStatus
)
from ai.protos.robotics_pb2_grpc import (
    AegisRoverServiceStub, AgriSwarmServiceStub, CanopyDroneServiceStub
)

logger = logging.getLogger(__name__)

class TestGRPCIntegration:
    """Comprehensive integration tests for gRPC contracts"""

    @pytest.fixture(scope="class")
    def grpc_server(self):
        """Start gRPC server with mock services"""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Add sensor services
        mycelial_service = MockMycelialProbeService()
        acoustic_service = MockAcousticPestMonitorService()
        management_service = MockSensorManagementService()

        add_MycelialProbeServiceServicer_to_server(mycelial_service, server)
        add_AcousticPestMonitorServiceServicer_to_server(acoustic_service, server)
        add_SensorManagementServiceServicer_to_server(management_service, server)

        # TODO: Add robotic services when implemented
        # add_AegisRoverServiceServicer_to_server(rover_service, server)
        # add_AgriSwarmServiceServicer_to_server(swarm_service, server)
        # add_CanopyDroneServiceServicer_to_server(drone_service, server)

        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("gRPC server started on port 50051")

        yield server

        server.stop(0)
        logger.info("gRPC server stopped")

    @pytest.fixture(scope="class")
    def sensor_simulators(self):
        """Set up sensor simulators"""
        manager = SensorSimulatorManager()

        # Add various sensor types
        manager.add_simulator(MockMycelialProbe("mycelial_001", zone_id=1))
        manager.add_simulator(MockMycelialProbe("mycelial_002", zone_id=1))
        manager.add_simulator(MockAcousticPestMonitor("acoustic_001", zone_id=2))
        manager.add_simulator(MockAcousticPestMonitor("acoustic_002", zone_id=2))

        manager.start_simulation(update_interval=0.5)
        logger.info("Sensor simulators started")

        yield manager

        manager.stop_simulation()
        logger.info("Sensor simulators stopped")

    @pytest.fixture(scope="class")
    def robotic_fleet(self):
        """Set up mock robotic fleet"""
        fleet = RoboticFleetManager()

        # Add different robot types
        fleet.add_robot(MockAegisRover("rover_001"))
        fleet.add_robot(MockAgriSwarmBot("swarm_001"))
        fleet.add_robot(MockAgriSwarmBot("swarm_002"))
        fleet.add_robot(MockCanopyDrone("drone_001"))

        fleet.connect_all("localhost", 50051)
        fleet.start_fleet_simulation(update_interval=1.0)
        logger.info("Robotic fleet simulation started")

        yield fleet

        fleet.disconnect_all()
        fleet.stop_fleet_simulation()
        logger.info("Robotic fleet simulation stopped")

    def test_sensor_registration_and_streaming(self, grpc_server, sensor_simulators):
        """Test sensor registration and real-time data streaming"""
        # Create gRPC client
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Register sensors
            for simulator in sensor_simulators.simulators.values():
                location = SensorLocation(
                    zone_id=simulator.zone_id,
                    position=Coordinate3D(
                        x=simulator.position["x"],
                        y=simulator.position["y"],
                        z=simulator.position["z"]
                    )
                )
                capabilities = SensorCapabilities(
                    supported_data_types=["biomass", "ph", "electrical_activity", "pest_activity"],
                    sampling_rate_hz=1.0,
                    battery_capacity_mah=2500.0,
                    supports_streaming=True,
                    supports_calibration=True,
                    communication_protocols=["grpc"]
                )

                request = SensorRegistration(
                    sensor_id=simulator.sensor_id,
                    sensor_type=simulator.sensor_type,
                    location=location,
                    capabilities=capabilities,
                    firmware_version="1.0.0"
                )

                response = management_stub.RegisterSensor(request)
                assert response.registered is True
                assert response.assigned_network_id.startswith("net_")
                assert response.initial_health.sensor_id == simulator.sensor_id
                logger.info(f"Registered sensor: {simulator.sensor_id}")

            # Test streaming data
            mycelial_stub = MycelialProbeServiceStub(channel)
            acoustic_stub = AcousticPestMonitorServiceStub(channel)

            mycelial_count = 0
            acoustic_count = 0

            for simulator in sensor_simulators.simulators.values():
                location = SensorLocation(
                    zone_id=simulator.zone_id,
                    position=Coordinate3D(
                        x=simulator.position["x"],
                        y=simulator.position["y"],
                        z=simulator.position["z"]
                    )
                )

                if simulator.sensor_type == SensorType.MYCELIAL_PROBE:
                    request = StreamMycelialDataRequest(
                        location=location,
                        sampling_interval_ms=100,
                        data_types=[MycelialDataType.MYCELIAL_BIOMASS, MycelialDataType.PH_LEVEL]
                    )
                    stream = mycelial_stub.StreamMycelialData(request)

                    for data in stream:
                        assert data.location.zone_id == simulator.zone_id
                        assert data.health.battery_level >= 0.0
                        assert data.health.battery_level <= 1.0
                        assert len(data.readings) > 0
                        mycelial_count += 1
                        if mycelial_count >= 3:
                            break

                elif simulator.sensor_type == SensorType.ACOUSTIC_MONITOR:
                    request = StreamAcousticDataRequest(
                        location=location,
                        sampling_interval_ms=100,
                        sensitivity_threshold=0.5,
                        target_pests=[PestType.APHID, PestType.BEETLE]
                    )
                    stream = acoustic_stub.StreamAcousticData(request)

                    for data in stream:
                        assert data.location.zone_id == simulator.zone_id
                        assert data.environment.background_noise_level >= 0.0
                        assert data.environment.background_noise_level <= 100.0
                        acoustic_count += 1
                        if acoustic_count >= 3:
                            break

            assert mycelial_count >= 1
            assert acoustic_count >= 1
            logger.info("Sensor streaming tests passed")

        finally:
            channel.close()

    def test_sensor_health_monitoring(self, grpc_server, sensor_simulators):
        """Test sensor health monitoring and status reporting"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test overall network health
            network_health = management_stub.GetSensorNetworkHealth(empty_pb2.Empty())
            assert network_health.total_sensors >= len(sensor_simulators.simulators)
            assert 0.0 <= network_health.average_battery_level <= 1.0
            assert 0 <= network_health.active_sensors <= network_health.total_sensors
            logger.info(
                f"Sensor network health: total={network_health.total_sensors}, active={network_health.active_sensors}"
            )

            # Test zone-level sensor retrieval
            registered_zones = set(sim.zone_id for sim in sensor_simulators.simulators.values())
            for zone_id in registered_zones:
                request = GetZoneSensorsRequest(zone_id=zone_id)
                response = management_stub.GetZoneSensors(request)
                assert response.zone_id == zone_id
                assert response.total_sensor_count >= 0
                logger.info(f"Zone {zone_id} sensors: {response.total_sensor_count}")

        finally:
            channel.close()

    def test_sensor_calibration(self, grpc_server, sensor_simulators):
        """Test sensor calibration procedures"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test bulk calibration for mycelial probes
            mycelial_ids = [sensor_id for sensor_id, simulator in sensor_simulators.simulators.items()
                            if simulator.sensor_type == SensorType.MYCELIAL_PROBE]
            if mycelial_ids:
                request = BulkCalibrationRequest(
                    sensor_ids=mycelial_ids,
                    calibration_type=CalibrationType.FIELD_CALIBRATION,
                    force_calibration=True
                )
                response = management_stub.BulkCalibrateSensors(request)
                assert response.total_requested == len(mycelial_ids)
                assert response.successfully_started >= 0
                for result in response.results:
                    assert result.sensor_id in mycelial_ids
                    assert isinstance(result.calibration_started, bool)
                logger.info(f"Bulk calibration results: {response.successfully_started}/{response.total_requested}")

        finally:
            channel.close()

    def test_emergency_shutdown(self, grpc_server, sensor_simulators):
        """Test emergency shutdown procedures"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test emergency shutdown on registered sensors
            sensor_ids = list(sensor_simulators.simulators.keys())
            request = EmergencyShutdownRequest(
                sensor_ids=sensor_ids,
                reason="Integration test emergency shutdown",
                immediate_shutdown=True
            )

            response = management_stub.EmergencyShutdown(request)
            assert response is not None
            logger.info("Emergency shutdown request completed")

        finally:
            channel.close()

    def test_concurrent_sensor_streams(self, grpc_server, sensor_simulators):
        """Test concurrent streaming from multiple sensors"""
        import concurrent.futures as cf

        def stream_sensor_data(sensor_id: str, simulator_type: SensorType, position: dict, zone_id: int):
            """Helper function to stream data from a single sensor"""
            channel = grpc.insecure_channel('localhost:50051')

            try:
                if simulator_type == SensorType.MYCELIAL_PROBE:
                    stub = MycelialProbeServiceStub(channel)
                    request = StreamMycelialDataRequest(
                        location=SensorLocation(
                            zone_id=zone_id,
                            position=Coordinate3D(x=position["x"], y=position["y"], z=position["z"])
                        ),
                        sampling_interval_ms=100,
                        data_types=[MycelialDataType.MYCELIAL_BIOMASS]
                    )
                    stream = stub.StreamMycelialData(request)
                elif simulator_type == SensorType.ACOUSTIC_MONITOR:
                    stub = AcousticPestMonitorServiceStub(channel)
                    request = StreamAcousticDataRequest(
                        location=SensorLocation(
                            zone_id=zone_id,
                            position=Coordinate3D(x=position["x"], y=position["y"], z=position["z"])
                        ),
                        sampling_interval_ms=100,
                        sensitivity_threshold=0.5,
                        target_pests=[PestType.APHID]
                    )
                    stream = stub.StreamAcousticData(request)
                else:
                    return False

                count = 0
                for data in stream:
                    count += 1
                    if count >= 3:  # Test 3 readings per sensor
                        break

                return count == 3

            finally:
                channel.close()

        # Test concurrent streaming from all sensors
        with cf.ThreadPoolExecutor(max_workers=len(sensor_simulators.simulators)) as executor:
            futures_list = []
            for sensor_id, simulator in sensor_simulators.simulators.items():
                future = executor.submit(
                    stream_sensor_data,
                    sensor_id,
                    simulator.sensor_type,
                    simulator.position,
                    simulator.zone_id
                )
                futures_list.append(future)

            # Wait for all streams to complete
            results = [future.result() for future in cf.as_completed(futures_list)]

        assert all(results) == True
        logger.info("Concurrent sensor streaming test passed")

    def test_sensor_network_resilience(self, grpc_server, sensor_simulators):
        """Test sensor network resilience and error handling"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test resilience for invalid zone query
            request = GetZoneSensorsRequest(zone_id=-1)
            response = management_stub.GetZoneSensors(request)
            assert response.total_sensor_count == 0
            assert len(response.sensors) == 0

            # Test resilience for empty network health request
            health_response = management_stub.GetSensorNetworkHealth(empty_pb2.Empty())
            assert health_response.total_sensors >= 0

            logger.info("Sensor network resilience test passed")

        finally:
            channel.close()

    def test_sensor_data_throughput(self, grpc_server, sensor_simulators):
        """Test sensor data throughput and performance"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            start_time = time.time()
            total_reads = 0

            # Collect network health for 5 seconds
            while time.time() - start_time < 5:
                response = management_stub.GetSensorNetworkHealth(empty_pb2.Empty())
                assert response is not None
                total_reads += 1
                time.sleep(0.1)

            elapsed_time = time.time() - start_time
            throughput = total_reads / elapsed_time

            assert throughput >= 8  # Lower threshold for more realistic performance
            logger.info(f"Throughput test passed: {throughput:.2f} health checks/second")

        finally:
            channel.close()

    def test_bulk_sensor_operations(self, grpc_server, sensor_simulators):
        """Test bulk sensor operations and management"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test bulk calibration
            mycelial_sensors = [
                sensor_id for sensor_id, sim in sensor_simulators.simulators.items()
                if sim.sensor_type == SensorType.MYCELIAL_PROBE
            ]

            if mycelial_sensors:
                request = BulkCalibrationRequest(
                    sensor_ids=mycelial_sensors,
                    calibration_type=CalibrationType.STANDARD_CALIBRATION,
                    force_calibration=False
                )

                response = management_stub.BulkCalibrateSensors(request)
                assert response.total_requested == len(mycelial_sensors)
                assert response.successfully_started >= 0
                logger.info(f"Bulk calibration: {response.successfully_started}/{response.total_requested} sensors calibrated")

            logger.info("Bulk sensor operations test passed")

            logger.info("Bulk sensor operations test passed")

        finally:
            channel.close()

    # TODO: Add robotic integration tests when robotic services are implemented
    # def test_robotic_command_execution(self, grpc_server, robotic_fleet):
    # def test_fleet_coordination(self, grpc_server, robotic_fleet):
    # def test_robotic_status_monitoring(self, grpc_server, robotic_fleet):

class TestSecurityValidation:
    """Security validation tests for gRPC contracts"""

    @pytest.fixture(scope="class")
    def grpc_server(self):
        """Start gRPC server with mock services"""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Add sensor services
        mycelial_service = MockMycelialProbeService()
        acoustic_service = MockAcousticPestMonitorService()
        management_service = MockSensorManagementService()

        add_MycelialProbeServiceServicer_to_server(mycelial_service, server)
        add_AcousticPestMonitorServiceServicer_to_server(acoustic_service, server)
        add_SensorManagementServiceServicer_to_server(management_service, server)

        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("gRPC server started on port 50051")

        yield server

        server.stop(0)
        logger.info("gRPC server stopped")

    def test_unauthorized_access_prevention(self, grpc_server):
        """Test that unauthorized access is prevented"""
        # TODO: Implement authentication/authorization tests
        # This would require implementing auth interceptors in the services
        pass

    def test_input_validation(self, grpc_server):
        """Test input validation and sanitization"""
        channel = grpc.insecure_channel('localhost:50051')
        mycelial_stub = MycelialProbeServiceStub(channel)

        try:
            # Test with malformed sensor location
            request = SensorLocation(zone_id=0, position=Coordinate3D(x=0, y=0, z=0))
            # This should work but return default health
            response = mycelial_stub.GetMycelialProbeHealth(request)
            assert response is not None

            # Test with negative zone ID
            request = SensorLocation(zone_id=-1, position=Coordinate3D(x=0, y=0, z=0))
            response = mycelial_stub.GetMycelialProbeHealth(request)
            assert response is not None

            logger.info("Input validation test passed")

        finally:
            channel.close()

class TestPerformanceValidation:
    """Performance validation tests for gRPC contracts"""

    @pytest.fixture(scope="class")
    def grpc_server(self):
        """Start gRPC server with mock services"""
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        # Add sensor services
        mycelial_service = MockMycelialProbeService()
        acoustic_service = MockAcousticPestMonitorService()
        management_service = MockSensorManagementService()

        add_MycelialProbeServiceServicer_to_server(mycelial_service, server)
        add_AcousticPestMonitorServiceServicer_to_server(acoustic_service, server)
        add_SensorManagementServiceServicer_to_server(management_service, server)

        server.add_insecure_port('[::]:50051')
        server.start()
        logger.info("gRPC server started on port 50051")

        yield server

        server.stop(0)
        logger.info("gRPC server stopped")

    def test_connection_pooling(self, grpc_server):
        """Test connection pooling and reuse"""
        # Create multiple channels
        channels = [grpc.insecure_channel('localhost:50051') for _ in range(10)]
        stubs = [SensorManagementServiceStub(ch) for ch in channels]

        try:
            # Test concurrent requests
            import concurrent.futures as cf

            def make_request(channel, sensor_type):
                if sensor_type == "mycelial":
                    mycelial_stub = MycelialProbeServiceStub(channel)
                    request = SensorLocation(zone_id=1, position=Coordinate3D(x=0, y=0, z=0))
                    try:
                        response = mycelial_stub.GetMycelialProbeHealth(request)
                        return response.sensor_id
                    except grpc.RpcError:
                        return None
                elif sensor_type == "acoustic":
                    acoustic_stub = AcousticPestMonitorServiceStub(channel)
                    request = SensorLocation(zone_id=1, position=Coordinate3D(x=0, y=0, z=0))
                    try:
                        response = acoustic_stub.GetAcousticSensorHealth(request)
                        return response.sensor_id
                    except grpc.RpcError:
                        return None
                else:
                    return None

            sensor_types = ["mycelial", "acoustic", "invalid"] * 10

            with cf.ThreadPoolExecutor(max_workers=10) as executor:
                futures_list = [
                    executor.submit(make_request, channel, sensor_type)
                    for channel, sensor_type in zip(channels, sensor_types)
                ]

                results = [future.result() for future in cf.as_completed(futures_list)]

            # Should handle mixed valid/invalid requests
            valid_results = [r for r in results if r is not None]
            assert len(valid_results) > 0

            logger.info("Connection pooling test passed")

        finally:
            for channel in channels:
                channel.close()

    def test_memory_usage(self, grpc_server):
        """Test memory usage under load"""
        # TODO: Implement memory profiling tests
        # This would require memory monitoring tools
        pass

    def test_error_recovery(self, grpc_server):
        """Test error recovery and resilience"""
        channel = grpc.insecure_channel('localhost:50051')
        mycelial_stub = MycelialProbeServiceStub(channel)

        try:
            # Test recovery from network issues (simulate by closing/reopening channel)
            channel.close()

            # Reconnect
            channel = grpc.insecure_channel('localhost:50051')
            mycelial_stub = MycelialProbeServiceStub(channel)

            # Should work after reconnection
            request = SensorLocation(zone_id=1, position=Coordinate3D(x=0, y=0, z=0))
            response = mycelial_stub.GetMycelialProbeHealth(request)
            assert response is not None

            logger.info("Error recovery test passed")

        finally:
            channel.close()
