import pytest
from datetime import datetime

from backend import models_db


def test_communication_network_and_broadcast_flow(client, test_db):
    headers = {"Authorization": "Bearer test-token"}

    # Create required tenant so foreign key constraints succeed
    db_session = test_db()
    tenant = models_db.Tenant(id=1, name="Test Tenant", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db_session.add(tenant)
    db_session.commit()

    network_payload = {
        "name": "Estate Mesh",
        "protocol": "mesh",
        "secure": True,
        "node_count": 5,
        "is_offline_ready": True,
        "metadata": {"band": "900MHz", "redundancy": "dual"}
    }

    network_response = client.post("/api/v1/communication/networks/register", json=network_payload, headers=headers)
    assert network_response.status_code == 200
    network_data = network_response.json()
    assert network_data["name"] == "Estate Mesh"
    assert network_data["protocol"] == "mesh"
    assert network_data["secure"] is True
    assert network_data["node_count"] == 5

    status_response = client.get("/api/v1/communication/status", headers=headers)
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["total_networks"] == 1
    assert status_data["secure_networks"] == 1
    assert status_data["offline_ready"] is True
    assert isinstance(status_data["recent_broadcasts"], list)

    broadcast_payload = {
        "message": "Test emergency alert",
        "priority": "high",
        "broadcast_type": "all",
        "target_zones": ["Lab", "Greenhouse"],
        "target_groups": ["staff", "security"]
    }

    broadcast_response = client.post("/api/v1/communication/broadcast/emergency", json=broadcast_payload, headers=headers)
    assert broadcast_response.status_code == 200
    broadcast_data = broadcast_response.json()
    assert broadcast_data["message"] == "Test emergency alert"
    assert broadcast_data["status"] in ("sent", "queued")

    queue_payload = {
        "destination": "backup.gateway",
        "payload": {"text": "Offline message test"},
        "priority": "normal",
        "metadata": {"origin": "dashboard"}
    }

    queue_response = client.post("/api/v1/communication/offline/queue", json=queue_payload, headers=headers)
    assert queue_response.status_code == 200
    queue_data = queue_response.json()
    assert queue_data["destination"] == "backup.gateway"
    assert queue_data["status"] == "queued"

    list_response = client.get("/api/v1/communication/offline/queue", headers=headers)
    assert list_response.status_code == 200
    offline_items = list_response.json()
    assert isinstance(offline_items, list)
    assert any(item["destination"] == "backup.gateway" for item in offline_items)
