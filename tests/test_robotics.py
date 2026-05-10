import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor


def auth_headers(client, email="robotics@example.com", password="testpass", tenant_name="Robotics Tenant"):
    client.post("/api/v1/tenants", json={"name": tenant_name})
    user_data = {
        "email": email,
        "password": password,
        "tenant_id": 1,
        "role": "admin"
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {"email": email, "password": password, "tenant_id": 1, "role": "admin"}
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_robotics_health_endpoint(client):
    headers = auth_headers(client)
    response = client.get("/api/v1/robotics/health", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("connected", "fallback")
    assert isinstance(data["connected"], bool)
    assert "service_address" in data


def test_robotics_register_and_task_routes(client):
    headers = auth_headers(client)
    register_payload = {
        "robot_id": "ROVER-001",
        "robot_type": "AEGIS_ROVER",
        "firmware_version": "v1.0.0",
        "model_year": 2026,
        "capabilities": {"navigation": "true", "payload_kg": "50"}
    }
    register_response = client.post("/api/v1/robotics/register", json=register_payload, headers=headers)
    assert register_response.status_code == 200
    register_data = register_response.json()
    assert register_data["status"] == "success"
    assert register_data["data"]["authenticated"] is True

    task_payload = {
        "task_id": "TASK-001",
        "robot_id": "ROVER-001",
        "operation_type": "HARVEST",
        "priority": 5,
        "task_detail": {"harvest": {"crop_id": "CRP-100", "location": {"x": 10.0, "y": 5.0, "z": 0.0}, "crop_species": "tomato", "estimated_yield_kg": 12, "use_gentle_mode": True}},
        "timeout_seconds": 120,
        "metadata": {"batch_id": "BATCH-001"}
    }
    task_response = client.post("/api/v1/robotics/tasks", json=task_payload, headers=headers)
    assert task_response.status_code == 200
    task_data = task_response.json()
    assert task_data["status"] == "success"
    assert task_data["data"]["task_id"] == "TASK-001"

    active_response = client.get("/api/v1/robotics/active", headers=headers)
    assert active_response.status_code == 200
    active_data = active_response.json()
    assert isinstance(active_data, list)
    assert len(active_data) >= 1


def test_robotics_concurrent_multi_robot_dispatch(client):
    """Test that multiple robots can be controlled concurrently."""
    headers = auth_headers(client)
    
    def send_robot_command(robot_id: int, task_id: int):
        task_payload = {
            "task_id": f"TASK-{task_id:03d}",
            "robot_id": f"ROVER-{robot_id:03d}",
            "operation_type": "NAVIGATE",
            "priority": 5,
            "task_detail": {"navigation": {"command_id": f"CMD-{task_id}", "target": {"x": float(robot_id), "y": 5.0, "z": 0.0}}},
            "timeout_seconds": 120,
        }
        response = client.post("/api/v1/robotics/tasks", json=task_payload, headers=headers)
        return response.status_code == 200
    
    # Simulate 10 robots sending tasks concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_robot_command, i, i) for i in range(1, 11)]
        results = [f.result() for f in futures]
    
    # All 10 concurrent requests should succeed
    assert all(results), f"Some requests failed: {results}"
    assert len(results) == 10


def test_robotics_fleet_coordination_and_optimization(client):
    headers = auth_headers(client)

    fleet_request = {
        "task_type": "HARVEST",
        "zone_id": "ZONE-1",
        "priority": 7,
        "robot_count": 3,
        "task_parameters": {"crop_type": "tomato", "harvest_priority": "high"}
    }
    fleet_response = client.post("/api/v1/robotics/fleet/coordinate", json=fleet_request, headers=headers)
    assert fleet_response.status_code == 200
    coord_data = fleet_response.json()
    assert coord_data["task_id"].startswith("fleet-HARVEST")
    assert coord_data["coordination_status"] in ("QUEUED", "STATUS_UNSPECIFIED")
    assert isinstance(coord_data["assigned_robots"], list)

    optimize_request = {
        "zone_id": "ZONE-1",
        "optimization_criteria": {"efficiency": 0.9, "safety": 0.95, "energy": 0.85}
    }
    optimize_response = client.post("/api/v1/robotics/fleet/optimize", json=optimize_request, headers=headers)
    assert optimize_response.status_code == 200
    opt_data = optimize_response.json()
    assert "optimization_id" in opt_data
    assert opt_data["zone_id"] == "ZONE-1"
    assert isinstance(opt_data["recommended_deployments"], list)

    status_response = client.get("/api/v1/robotics/fleet/status?zone_id=ZONE-1", headers=headers)
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["total_robots"] >= 0
    assert "zone_status" in status_data

    emergency_request = {"zone_id": "ZONE-1", "reason": "maintenance"}
    emergency_response = client.post("/api/v1/robotics/fleet/emergency-stop", json=emergency_request, headers=headers)
    assert emergency_response.status_code == 200
    emergency_data = emergency_response.json()
    assert emergency_data["emergency_stop_issued"] is True
    assert emergency_data["reason"] == "maintenance"
