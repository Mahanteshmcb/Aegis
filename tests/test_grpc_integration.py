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
    MycelialProbeService, AcousticPestMonitorService, SensorManagementService
)
from ai.protos.sensors_pb2 import (
    SensorData, SensorType, CalibrationType, HealthStatus,
    StreamSensorDataRequest, RegisterSensorRequest, CalibrationRequest,
    EmergencyShutdownRequest, SensorHealthRequest
)
from ai.protos.sensors_pb2_grpc import (
    MycelialProbeServiceStub, AcousticPestMonitorServiceStub,
    SensorManagementServiceStub, add_MycelialProbeServiceServicer_to_server,
    add_AcousticPestMonitorServiceServicer_to_server,
    add_SensorManagementServiceServicer_to_server
)
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
        mycelial_service = MycelialProbeService()
        acoustic_service = AcousticPestMonitorService()
        management_service = SensorManagementService()

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
                request = RegisterSensorRequest(
                    sensor_id=simulator.sensor_id,
                    sensor_type=simulator.sensor_type,
                    zone_id=simulator.zone_id,
                    position=simulator.position
                )

                response = management_stub.RegisterSensor(request)
                assert response.success == True
                assert response.sensor_id == simulator.sensor_id
                logger.info(f"Registered sensor: {simulator.sensor_id}")

            # Test streaming data
            mycelial_stub = MycelialProbeServiceStub(channel)
            acoustic_stub = AcousticPestMonitorServiceStub(channel)

            # Stream from mycelial probes
            mycelial_request = StreamSensorDataRequest(sensor_ids=["mycelial_001", "mycelial_002"])
            mycelial_stream = mycelial_stub.StreamSensorData(mycelial_request)

            mycelial_count = 0
            for data in mycelial_stream:
                assert data.sensor_id in ["mycelial_001", "mycelial_002"]
                assert data.mycelial_probe_data.biomass_density >= 0
                assert data.mycelial_probe_data.biomass_density <= 1.0
                assert 4.0 <= data.mycelial_probe_data.ph_level <= 8.0
                mycelial_count += 1
                if mycelial_count >= 5:  # Test first 5 readings
                    break

            assert mycelial_count == 5
            logger.info("Mycelial probe streaming test passed")

            # Stream from acoustic monitors
            acoustic_request = StreamSensorDataRequest(sensor_ids=["acoustic_001", "acoustic_002"])
            acoustic_stream = acoustic_stub.StreamSensorData(acoustic_request)

            acoustic_count = 0
            for data in acoustic_stream:
                assert data.sensor_id in ["acoustic_001", "acoustic_002"]
                assert 0 <= data.acoustic_pest_data.pest_activity_level <= 1.0
                acoustic_count += 1
                if acoustic_count >= 5:  # Test first 5 readings
                    break

            assert acoustic_count == 5
            logger.info("Acoustic pest monitor streaming test passed")

        finally:
            channel.close()

    def test_sensor_health_monitoring(self, grpc_server, sensor_simulators):
        """Test sensor health monitoring and status reporting"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test health check for all sensors
            for sensor_id in sensor_simulators.simulators.keys():
                request = SensorHealthRequest(sensor_id=sensor_id)
                response = management_stub.GetSensorHealth(request)

                assert response.sensor_id == sensor_id
                assert response.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.CRITICAL]
                assert 0 <= response.battery_level <= 100
                assert 0 <= response.signal_strength <= 100
                logger.info(f"Health check for {sensor_id}: {response.status}, battery: {response.battery_level}%")

        finally:
            channel.close()

    def test_sensor_calibration(self, grpc_server, sensor_simulators):
        """Test sensor calibration procedures"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test calibration for mycelial probes
            for sensor_id, simulator in sensor_simulators.simulators.items():
                if simulator.sensor_type == SensorType.MYCELIAL_PROBE:
                    request = CalibrationRequest(
                        sensor_id=sensor_id,
                        calibration_type=CalibrationType.PH_CALIBRATION,
                        parameters={"target_ph": 7.0}
                    )

                    response = management_stub.CalibrateSensor(request)
                    assert response.success == True
                    assert response.sensor_id == sensor_id
                    assert "calibration" in response.message.lower()
                    logger.info(f"Calibrated {sensor_id}: {response.message}")

        finally:
            channel.close()

    def test_emergency_shutdown(self, grpc_server, sensor_simulators):
        """Test emergency shutdown procedures"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test emergency shutdown
            request = EmergencyShutdownRequest(
                reason="Integration test emergency shutdown",
                affected_zones=[1, 2]
            )

            response = management_stub.EmergencyShutdown(request)
            assert response.success == True
            assert len(response.shutdown_sensors) > 0
            assert "emergency" in response.message.lower()
            logger.info(f"Emergency shutdown completed: {response.message}")

        finally:
            channel.close()

    def test_concurrent_sensor_streams(self, grpc_server, sensor_simulators):
        """Test concurrent streaming from multiple sensors"""
        import concurrent.futures as cf

        def stream_sensor_data(sensor_id: str, expected_type: SensorType):
            """Helper function to stream data from a single sensor"""
            channel = grpc.insecure_channel('localhost:50051')

            try:
                if expected_type == SensorType.MYCELIAL_PROBE:
                    stub = MycelialProbeServiceStub(channel)
                elif expected_type == SensorType.ACOUSTIC_PEST_MONITOR:
                    stub = AcousticPestMonitorServiceStub(channel)
                else:
                    return False

                request = StreamSensorDataRequest(sensor_ids=[sensor_id])
                stream = stub.StreamSensorData(request)

                count = 0
                for data in stream:
                    assert data.sensor_id == sensor_id
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
                future = executor.submit(stream_sensor_data, sensor_id, simulator.sensor_type)
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
            # Test with invalid sensor ID
            request = SensorHealthRequest(sensor_id="invalid_sensor_123")
            with pytest.raises(grpc.RpcError) as exc_info:
                management_stub.GetSensorHealth(request)
            assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND

            # Test with empty sensor list
            stream_request = StreamSensorDataRequest(sensor_ids=[])
            mycelial_stub = MycelialProbeServiceStub(channel)
            stream = mycelial_stub.StreamSensorData(stream_request)

            # Should return empty stream
            data_list = list(stream)
            assert len(data_list) == 0

            logger.info("Sensor network resilience test passed")

        finally:
            channel.close()

    @pytest.mark.asyncio
    async def test_sensor_data_throughput(self, grpc_server, sensor_simulators):
        """Test sensor data throughput and performance"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            start_time = time.time()
            total_readings = 0

            # Collect data for 5 seconds
            while time.time() - start_time < 5:
                for sensor_id in sensor_simulators.simulators.keys():
                    request = SensorHealthRequest(sensor_id=sensor_id)
                    response = management_stub.GetSensorHealth(request)
                    total_readings += 1

                await asyncio.sleep(0.1)  # Small delay to prevent overwhelming

            elapsed_time = time.time() - start_time
            throughput = total_readings / elapsed_time

            # Should handle at least 10 readings per second
            assert throughput >= 10
            logger.info(f"Throughput test passed: {throughput:.2f} readings/second")

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

            for sensor_id in mycelial_sensors:
                request = CalibrationRequest(
                    sensor_id=sensor_id,
                    calibration_type=CalibrationType.BULK_CALIBRATION,
                    parameters={"calibration_mode": "comprehensive"}
                )

                response = management_stub.CalibrateSensor(request)
                assert response.success == True
                logger.info(f"Bulk calibration for {sensor_id}: {response.message}")

            logger.info("Bulk sensor operations test passed")

        finally:
            channel.close()

    # TODO: Add robotic integration tests when robotic services are implemented
    # def test_robotic_command_execution(self, grpc_server, robotic_fleet):
    # def test_fleet_coordination(self, grpc_server, robotic_fleet):
    # def test_robotic_status_monitoring(self, grpc_server, robotic_fleet):

class TestSecurityValidation:
    """Security validation tests for gRPC contracts"""

    def test_unauthorized_access_prevention(self, grpc_server):
        """Test that unauthorized access is prevented"""
        # TODO: Implement authentication/authorization tests
        # This would require implementing auth interceptors in the services
        pass

    def test_input_validation(self, grpc_server):
        """Test input validation and sanitization"""
        channel = grpc.insecure_channel('localhost:50051')
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test with malformed sensor ID
            request = SensorHealthRequest(sensor_id="")
            with pytest.raises(grpc.RpcError):
                management_stub.GetSensorHealth(request)

            # Test with extremely long sensor ID
            long_id = "sensor_" + "x" * 1000
            request = SensorHealthRequest(sensor_id=long_id)
            with pytest.raises(grpc.RpcError):
                management_stub.GetSensorHealth(request)

            logger.info("Input validation test passed")

        finally:
            channel.close()

class TestPerformanceValidation:
    """Performance validation tests for gRPC contracts"""

    def test_connection_pooling(self, grpc_server):
        """Test connection pooling and reuse"""
        # Create multiple channels
        channels = [grpc.insecure_channel('localhost:50051') for _ in range(10)]
        stubs = [SensorManagementServiceStub(ch) for ch in channels]

        try:
            # Test concurrent requests
            import concurrent.futures as cf

            def make_request(stub, sensor_id):
                request = SensorHealthRequest(sensor_id=sensor_id)
                try:
                    response = stub.GetSensorHealth(request)
                    return response.sensor_id
                except grpc.RpcError:
                    return None

            sensor_ids = ["mycelial_001", "acoustic_001", "invalid_sensor"] * 10

            with cf.ThreadPoolExecutor(max_workers=10) as executor:
                futures_list = [
                    executor.submit(make_request, stub, sensor_id)
                    for stub, sensor_id in zip(stubs, sensor_ids)
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
        management_stub = SensorManagementServiceStub(channel)

        try:
            # Test recovery from network issues (simulate by closing/reopening channel)
            channel.close()

            # Reconnect
            channel = grpc.insecure_channel('localhost:50051')
            management_stub = SensorManagementServiceStub(channel)

            # Should work after reconnection
            request = SensorHealthRequest(sensor_id="mycelial_001")
            response = management_stub.GetSensorHealth(request)
            assert response.sensor_id == "mycelial_001"

            logger.info("Error recovery test passed")

        finally:
            channel.close()</content>
<parameter name="filePath">tests/test_grpc_integration.py