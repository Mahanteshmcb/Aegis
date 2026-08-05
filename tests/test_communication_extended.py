"""
Test suite for extended communication router covering all five communication layers:
1. Robot communication channels
2. Device communication channels
3. Zone communication channels
4. Server communication channels
5. Vryndara AI communication channels
6. Cross-layer orchestration
"""

import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from backend.main import app
from backend.database import Base, engine
from backend.dependencies import get_current_user, get_db
from backend import models_db
from sqlalchemy.orm import sessionmaker, Session


# Setup test database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create test user
TEST_USER = {
    "sub": "test@example.com",
    "email": "test@example.com",
    "tenant_id": 1,
    "role": "admin"
}


def override_get_current_user():
    return TEST_USER


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before tests and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client with dependency overrides."""
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test tenant
    db = SessionLocal()
    tenant = models_db.Tenant(name="test-tenant", settings={})
    db.add(tenant)
    db.commit()
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    db.close()


class TestRobotCommunication:
    """Test robot communication channel endpoints."""

    def test_create_robot_channel(self, client):
        """Test creating a robot communication channel."""
        response = client.post(
            "/api/v1/communication/robots/channels",
            json={
                "channel_name": "fleet-primary",
                "protocol": "grpc",
                "robot_ids": ["robot-001", "robot-002", "robot-003"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel_name"] == "fleet-primary"
        assert data["protocol"] == "grpc"
        assert len(data["robot_ids"]) == 3
        assert data["active_robots"] == 3
        assert data["status"] == "connected"

    def test_list_robot_channels(self, client):
        """Test listing robot communication channels."""
        # Create two channels
        client.post(
            "/api/v1/communication/robots/channels",
            json={
                "channel_name": "fleet-1",
                "protocol": "grpc",
                "robot_ids": ["robot-001"]
            }
        )
        client.post(
            "/api/v1/communication/robots/channels",
            json={
                "channel_name": "fleet-2",
                "protocol": "mqtt",
                "robot_ids": ["robot-002"]
            }
        )

        response = client.get("/api/v1/communication/robots/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_robot_channel_heartbeat(self, client):
        """Test updating robot channel heartbeat."""
        # Create channel
        create_response = client.post(
            "/api/v1/communication/robots/channels",
            json={
                "channel_name": "fleet-primary",
                "protocol": "grpc",
                "robot_ids": ["robot-001"]
            }
        )
        channel_id = create_response.json()["id"]

        # Send heartbeat
        response = client.post(f"/api/v1/communication/robots/channels/{channel_id}/heartbeat")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["last_heartbeat"] is not None


class TestDeviceCommunication:
    """Test device communication channel endpoints."""

    def test_create_device_channel(self, client):
        """Test creating a device communication channel."""
        response = client.post(
            "/api/v1/communication/devices/channels",
            json={
                "channel_name": "sensor-mesh",
                "protocol": "mqtt",
                "device_ids": ["sensor-001", "sensor-002"],
                "mesh_topology": "mesh"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel_name"] == "sensor-mesh"
        assert data["protocol"] == "mqtt"
        assert len(data["device_ids"]) == 2
        assert data["mesh_topology"] == "mesh"

    def test_list_device_channels(self, client):
        """Test listing device communication channels."""
        client.post(
            "/api/v1/communication/devices/channels",
            json={
                "channel_name": "sensors-1",
                "protocol": "mqtt",
                "device_ids": ["sensor-001"],
                "mesh_topology": "star"
            }
        )
        
        response = client.get("/api/v1/communication/devices/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_device_channel_sync(self, client):
        """Test device channel synchronization."""
        # Create channel
        create_response = client.post(
            "/api/v1/communication/devices/channels",
            json={
                "channel_name": "sensors-primary",
                "protocol": "mqtt",
                "device_ids": ["sensor-001"]
            }
        )
        channel_id = create_response.json()["id"]

        # Sync channel
        response = client.post(f"/api/v1/communication/devices/channels/{channel_id}/sync")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        assert data["last_sync"] is not None


class TestZoneCommunication:
    """Test zone communication channel endpoints."""

    def test_create_zone_channel(self, client):
        """Test creating a zone communication channel."""
        # Create a zone first
        db = SessionLocal()
        zone = models_db.Zone(tenant_id=1, name="zone-1", description="Test Zone")
        db.add(zone)
        db.commit()
        zone_id = zone.id
        db.close()

        response = client.post(
            "/api/v1/communication/zones/channels",
            json={
                "zone_id": zone_id,
                "channel_name": "zone-mesh",
                "protocol": "mqtt",
                "connected_zones": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["zone_id"] == zone_id
        assert data["channel_name"] == "zone-mesh"

    def test_get_zone_channel(self, client):
        """Test retrieving zone communication channel."""
        # Create a zone and channel
        db = SessionLocal()
        zone = models_db.Zone(tenant_id=1, name="zone-2", description="Test Zone")
        db.add(zone)
        db.commit()
        zone_id = zone.id
        db.close()

        client.post(
            "/api/v1/communication/zones/channels",
            json={
                "zone_id": zone_id,
                "channel_name": "zone-channel",
                "protocol": "mqtt"
            }
        )

        response = client.get(f"/api/v1/communication/zones/{zone_id}/channel")
        assert response.status_code == 200
        data = response.json()
        assert data["zone_id"] == zone_id


class TestServerCommunication:
    """Test server communication channel endpoints."""

    def test_register_server_channel(self, client):
        """Test registering a server in communication mesh."""
        response = client.post(
            "/api/v1/communication/servers/channels",
            json={
                "server_id": "api-server-01",
                "server_name": "Primary API Server",
                "protocol": "grpc",
                "peer_servers": ["api-server-02"],
                "is_primary": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["server_id"] == "api-server-01"
        assert data["is_primary"] is True
        assert data["status"] == "healthy"

    def test_list_server_channels(self, client):
        """Test listing all servers in mesh."""
        client.post(
            "/api/v1/communication/servers/channels",
            json={
                "server_id": "api-server-01",
                "server_name": "Primary API",
                "protocol": "grpc",
                "is_primary": True
            }
        )
        client.post(
            "/api/v1/communication/servers/channels",
            json={
                "server_id": "api-server-02",
                "server_name": "Secondary API",
                "protocol": "grpc",
                "is_primary": False
            }
        )

        response = client.get("/api/v1/communication/servers/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Primary should be first
        assert data[0]["is_primary"] is True

    def test_server_health_check(self, client):
        """Test server health check update."""
        # Register server
        create_response = client.post(
            "/api/v1/communication/servers/channels",
            json={
                "server_id": "api-server-01",
                "server_name": "Test Server",
                "protocol": "grpc"
            }
        )

        # Update health
        response = client.post(
            "/api/v1/communication/servers/api-server-01/health-check",
            params={"health_score": 85.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["health_score"] == 85.0
        assert data["status"] == "healthy"


class TestVryndaraCommunication:
    """Test Vryndara AI service communication endpoints."""

    def test_configure_vryndara_channel(self, client):
        """Test configuring Vryndara communication channel."""
        response = client.post(
            "/api/v1/communication/vryndara/channel/configure",
            json={
                "service_endpoint": "grpc://vryndara-ai:50051",
                "protocol": "grpc",
                "request_timeout_ms": 5000,
                "max_concurrent_requests": 100
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["service_endpoint"] == "grpc://vryndara-ai:50051"
        assert data["status"] == "connected"

    def test_get_vryndara_channel(self, client):
        """Test retrieving Vryndara channel status."""
        # Configure channel first
        client.post(
            "/api/v1/communication/vryndara/channel/configure",
            json={
                "service_endpoint": "grpc://vryndara-ai:50051",
                "protocol": "grpc"
            }
        )

        response = client.get("/api/v1/communication/vryndara/channel")
        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["status"] == "connected"

    def test_record_vryndara_request(self, client):
        """Test recording Vryndara request statistics."""
        # Configure channel first
        client.post(
            "/api/v1/communication/vryndara/channel/configure",
            json={
                "service_endpoint": "grpc://vryndara-ai:50051",
                "protocol": "grpc"
            }
        )

        # Record successful request
        response = client.post(
            "/api/v1/communication/vryndara/request",
            params={"success": True, "latency_ms": 150.0}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["successful_requests"] == 1
        assert data["failed_requests"] == 0


class TestCommunicationOrchestration:
    """Test cross-layer communication orchestration."""

    def test_create_orchestration_route(self, client):
        """Test creating a cross-layer communication route."""
        response = client.post(
            "/api/v1/communication/orchestration/routes",
            json={
                "orchestration_type": "fleet_to_zone",
                "source_type": "robot",
                "target_type": "zone",
                "source_id": "robot-001",
                "target_id": "zone-1",
                "routing_priority": 10
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["orchestration_type"] == "fleet_to_zone"
        assert data["source_type"] == "robot"
        assert data["status"] == "active"

    def test_list_orchestration_routes(self, client):
        """Test listing all orchestration routes."""
        client.post(
            "/api/v1/communication/orchestration/routes",
            json={
                "orchestration_type": "fleet_to_zone",
                "source_type": "robot",
                "target_type": "zone",
                "source_id": "robot-001",
                "target_id": "zone-1"
            }
        )
        client.post(
            "/api/v1/communication/orchestration/routes",
            json={
                "orchestration_type": "device_to_server",
                "source_type": "device",
                "target_type": "server",
                "source_id": "sensor-001",
                "target_id": "api-server-01"
            }
        )

        response = client.get("/api/v1/communication/orchestration/routes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2


class TestFullCommunicationStatus:
    """Test unified communication status endpoint."""

    def test_get_full_communication_status(self, client):
        """Test retrieving comprehensive communication infrastructure status."""
        # Create some channels across all types
        db = SessionLocal()
        zone = models_db.Zone(tenant_id=1, name="zone-1", description="Test")
        db.add(zone)
        db.commit()
        zone_id = zone.id
        db.close()

        # Robot channel
        client.post(
            "/api/v1/communication/robots/channels",
            json={"channel_name": "fleet", "protocol": "grpc", "robot_ids": ["robot-001"]}
        )

        # Device channel
        client.post(
            "/api/v1/communication/devices/channels",
            json={"channel_name": "sensors", "protocol": "mqtt", "device_ids": ["sensor-001"]}
        )

        # Zone channel
        client.post(
            "/api/v1/communication/zones/channels",
            json={"zone_id": zone_id, "channel_name": "zone-ch", "protocol": "mqtt"}
        )

        # Server channel
        client.post(
            "/api/v1/communication/servers/channels",
            json={"server_id": "api-01", "server_name": "API", "protocol": "grpc"}
        )

        # Vryndara channel
        client.post(
            "/api/v1/communication/vryndara/channel/configure",
            json={"service_endpoint": "grpc://vryndara:50051", "protocol": "grpc"}
        )

        response = client.get("/api/v1/communication/full-status")
        assert response.status_code == 200
        data = response.json()
        assert len(data["robot_channels"]) == 1
        assert len(data["device_channels"]) == 1
        assert len(data["zone_channels"]) == 1
        assert len(data["server_channels"]) == 1
        assert data["vryndara_channel"] is not None
        assert data["overall_health"] > 0
