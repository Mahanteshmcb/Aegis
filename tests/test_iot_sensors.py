# Tests for IoT Sensor Services
# Comprehensive testing of gRPC sensor services and REST API endpoints
# Day 36: gRPC service definitions for IoT sensors

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime

from ai.sensor_connector import SensorConnector
from ai.protos.sensors_pb2 import SensorType, CalibrationType, SensorStatus


class TestSensorConnector:
    """Test suite for the IoT Sensor Connector."""

    @pytest.fixture
    async def setup_connector(self):
        """Set up test sensor connector."""
        connector = SensorConnector()
        yield connector
        await connector.disconnect()

    @pytest.mark.asyncio
    async def test_sensor_registration(self, setup_connector):
        """Test registering a new sensor."""
        connector = setup_connector

        with patch.object(connector, '_get_management_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the RegisterSensor response
            mock_response = AsyncMock()
            mock_response.registered = True
            mock_stub.RegisterSensor.return_value = mock_response

            success = await connector.register_sensor(
                "test_sensor_001",
                SensorType.MYCELIAL_PROBE,
                1,
                (10.0, 5.0, 0.5)
            )

            assert success is True
            mock_stub.RegisterSensor.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_zone_sensors(self, setup_connector):
        """Test retrieving sensors for a zone."""
        connector = setup_connector

        with patch.object(connector, '_get_management_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the GetZoneSensors response
            mock_response = AsyncMock()
            mock_response.sensors = []
            mock_response.total_sensor_count = 0
            mock_stub.GetZoneSensors.return_value = mock_response

            response = await connector.get_zone_sensors(1)

            assert response.total_sensor_count == 0
            assert len(response.sensors) == 0
            mock_stub.GetZoneSensors.assert_called_once()

    @pytest.mark.asyncio
    async def test_mycelial_status_retrieval(self, setup_connector):
        """Test getting mycelial network status."""
        connector = setup_connector

        with patch.object(connector, '_get_mycelial_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the GetMycelialStatus response
            mock_response = AsyncMock()
            mock_response.network_state = 2  # ACTIVE
            mock_response.biomass_density = 0.75
            mock_response.alerts = []
            mock_stub.GetMycelialStatus.return_value = mock_response

            status = await connector.get_mycelial_status(1, (10.0, 5.0, 0.5))

            assert status.network_state == 2
            assert status.biomass_density == 0.75
            mock_stub.GetMycelialStatus.assert_called_once()

    @pytest.mark.asyncio
    async def test_pest_activity_status(self, setup_connector):
        """Test getting pest activity status."""
        connector = setup_connector

        with patch.object(connector, '_get_acoustic_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the GetPestActivityStatus response
            mock_response = AsyncMock()
            mock_response.pest_levels = []
            mock_response.alerts = []
            mock_stub.GetPestActivityStatus.return_value = mock_response

            status = await connector.get_pest_activity_status(1, (10.0, 5.0, 0.5))

            assert len(status.pest_levels) == 0
            assert len(status.alerts) == 0
            mock_stub.GetPestActivityStatus.assert_called_once()

    @pytest.mark.asyncio
    async def test_pest_scan_trigger(self, setup_connector):
        """Test triggering a pest scan."""
        connector = setup_connector

        with patch.object(connector, '_get_acoustic_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the TriggerPestScan response
            mock_response = AsyncMock()
            mock_response.scan_started = True
            mock_response.scan_id = "scan_123"
            mock_stub.TriggerPestScan.return_value = mock_response

            success = await connector.trigger_pest_scan(1, (10.0, 5.0, 0.5), 60)

            assert success is True
            mock_stub.TriggerPestScan.assert_called_once()

    @pytest.mark.asyncio
    async def test_sensor_calibration(self, setup_connector):
        """Test calibrating a sensor."""
        connector = setup_connector

        # Test mycelial probe calibration
        with patch.object(connector, '_get_mycelial_stub', return_value=AsyncMock()) as mock_stub:
            mock_response = AsyncMock()
            mock_response.calibration_started = True
            mock_stub.CalibrateMycelialProbe.return_value = mock_response

            success = await connector.calibrate_sensor("myco_001", CalibrationType.STANDARD_CALIBRATION)

            assert success is True
            mock_stub.CalibrateMycelialProbe.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_calibration(self, setup_connector):
        """Test bulk sensor calibration."""
        connector = setup_connector

        with patch.object(connector, '_get_management_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the BulkCalibrateSensors response
            mock_response = AsyncMock()
            mock_response.total_requested = 3
            mock_response.successfully_started = 2
            mock_response.results = []
            mock_stub.BulkCalibrateSensors.return_value = mock_response

            count = await connector.bulk_calibrate_sensors(
                ["sensor_001", "sensor_002", "sensor_003"],
                CalibrationType.STANDARD_CALIBRATION
            )

            assert count == 2
            mock_stub.BulkCalibrateSensors.assert_called_once()

    @pytest.mark.asyncio
    async def test_emergency_shutdown(self, setup_connector):
        """Test emergency sensor shutdown."""
        connector = setup_connector

        with patch.object(connector, '_get_management_stub', return_value=AsyncMock()) as mock_stub:
            mock_stub.EmergencyShutdown.return_value = None

            success = await connector.emergency_shutdown(
                ["sensor_001", "sensor_002"],
                "System maintenance"
            )

            assert success is True
            mock_stub.EmergencyShutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_sensor_health_retrieval(self, setup_connector):
        """Test getting sensor health status."""
        connector = setup_connector

        with patch.object(connector, '_get_mycelial_stub', return_value=AsyncMock()) as mock_stub:
            # Mock the GetMycelialProbeHealth response
            mock_response = AsyncMock()
            mock_response.sensor_id = "myco_001"
            mock_response.status = SensorStatus.SENSOR_ACTIVE
            mock_response.battery_level = 0.85
            mock_response.signal_strength = 0.92
            mock_stub.GetMycelialProbeHealth.return_value = mock_response

            health = await connector.get_sensor_health("myco_001")

            assert health.sensor_id == "myco_001"
            assert health.status == SensorStatus.SENSOR_ACTIVE
            assert health.battery_level == 0.85
            mock_stub.GetMycelialProbeHealth.assert_called_once()


class TestSensorServicesIntegration:
    """Integration tests for sensor services (would require running gRPC server)."""

    @pytest.mark.asyncio
    async def test_full_sensor_workflow(self):
        """Test complete sensor registration and monitoring workflow."""
        # This would test the full integration with running sensor services
        # For now, just verify the connector can be instantiated
        connector = SensorConnector()

        # Verify connector has expected methods
        assert hasattr(connector, 'connect')
        assert hasattr(connector, 'register_sensor')
        assert hasattr(connector, 'get_zone_sensors')
        assert hasattr(connector, 'stream_mycelial_data')
        assert hasattr(connector, 'stream_acoustic_data')

    def test_protobuf_imports(self):
        """Test that protobuf generated code can be imported."""
        try:
            from ai.protos import sensors_pb2, sensors_pb2_grpc
            # Verify key classes exist
            assert hasattr(sensors_pb2, 'SensorLocation')
            assert hasattr(sensors_pb2, 'MycelialData')
            assert hasattr(sensors_pb2, 'AcousticData')
            assert hasattr(sensors_pb2_grpc, 'MycelialProbeServiceStub')
            assert hasattr(sensors_pb2_grpc, 'AcousticPestMonitorServiceStub')
        except ImportError as e:
            pytest.fail(f"Failed to import protobuf modules: {e}")


# Mock sensor service implementations for testing
class MockSensorServiceTest:
    """Test the mock sensor service implementations."""

    def test_mock_mycelial_service_initialization(self):
        """Test that mock mycelial service can be instantiated."""
        from ai.sensor_services import MockMycelialProbeService

        service = MockMycelialProbeService()
        assert service.active_sensors == {}
        assert service.mycelial_data_history == {}

    def test_mock_acoustic_service_initialization(self):
        """Test that mock acoustic service can be instantiated."""
        from ai.sensor_services import MockAcousticPestMonitorService

        service = MockAcousticPestMonitorService()
        assert service.active_scans == {}

    def test_mock_management_service_initialization(self):
        """Test that mock management service can be instantiated."""
        from ai.sensor_services import MockSensorManagementService

        service = MockSensorManagementService()
        assert service.registered_sensors == {}
        assert service.network_health.total_sensors == 0


if __name__ == "__main__":
    pytest.main([__file__])