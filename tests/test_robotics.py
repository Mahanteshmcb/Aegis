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


def test_robotics_task_scheduling_and_assignment(client):
    headers = auth_headers(client)

    enqueue_payloads = [
        {
            "task_id": "SCHED-001",
            "operation_type": "HARVEST",
            "priority": 7,
            "zone_id": "ZONE-1",
            "task_detail": {"harvest": {"crop_id": "CRP-001", "location": {"x": 1.0, "y": 2.0, "z": 0.0}}},
        },
        {
            "task_id": "SCHED-002",
            "operation_type": "PLANT",
            "priority": 9,
            "zone_id": "ZONE-1",
            "task_detail": {"plant": {"species": "beans", "position": {"x": 2.0, "y": 3.0, "z": 0.0}}},
        },
        {
            "task_id": "SCHED-003",
            "operation_type": "SPRAY",
            "priority": 5,
            "zone_id": "ZONE-2",
            "task_detail": {"spray": {"product": "biofungicide", "area": "sector_a"}},
        },
    ]

    for payload in enqueue_payloads:
        response = client.post("/api/v1/robotics/schedule/enqueue", json=payload, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["task_id"] == payload["task_id"]

    queue_response = client.get("/api/v1/robotics/schedule/queue", headers=headers)
    assert queue_response.status_code == 200
    queue_data = queue_response.json()
    assert queue_data["status"] == "success"
    assert queue_data["data"]["queue_length"] == 3
    assert any(task["task_id"] == "SCHED-002" for task in queue_data["data"]["tasks"])

    assign_response = client.post("/api/v1/robotics/schedule/assign", headers=headers)
    assert assign_response.status_code == 200
    assign_data = assign_response.json()
    assert assign_data["status"] == "success"
    assert assign_data["data"]["assigned_count"] >= 1
    assert isinstance(assign_data["data"]["assigned_tasks"], list)
    assert assign_data["data"]["queue_length"] == 3

    persisted_queue_response = client.get("/api/v1/robotics/schedule/queue", headers=headers)
    assert persisted_queue_response.status_code == 200
    persisted_queue_data = persisted_queue_response.json()
    assert persisted_queue_data["status"] == "success"
    assert persisted_queue_data["data"]["queue_length"] == 3
    assert any(task["status"] in ("assigned", "conflicted", "pending") for task in persisted_queue_data["data"]["tasks"])


def test_robotics_cancel_scheduled_task(client):
    headers = auth_headers(client)

    # First enqueue a task
    enqueue_payload = {
        "task_id": "CANCEL-TEST-001",
        "operation_type": "HARVEST",
        "priority": 5,
        "zone_id": "ZONE-1",
        "task_detail": {"harvest": {"crop_id": "CRP-001", "location": {"x": 1.0, "y": 2.0, "z": 0.0}}},
    }
    enqueue_response = client.post("/api/v1/robotics/schedule/enqueue", json=enqueue_payload, headers=headers)
    assert enqueue_response.status_code == 200

    # Verify it's in the queue
    queue_response = client.get("/api/v1/robotics/schedule/queue", headers=headers)
    assert queue_response.status_code == 200
    queue_data = queue_response.json()
    assert queue_data["data"]["queue_length"] >= 1
    assert any(task["task_id"] == "CANCEL-TEST-001" for task in queue_data["data"]["tasks"])

    # Cancel the task
    cancel_response = client.delete("/api/v1/robotics/schedule/cancel/CANCEL-TEST-001", headers=headers)
    assert cancel_response.status_code == 200
    cancel_data = cancel_response.json()
    assert cancel_data["status"] == "success"
    assert cancel_data["data"]["task_id"] == "CANCEL-TEST-001"

    # Verify it's no longer in the queue
    queue_response_after = client.get("/api/v1/robotics/schedule/queue", headers=headers)
    assert queue_response_after.status_code == 200
    queue_data_after = queue_response_after.json()
    assert queue_data_after["data"]["queue_length"] == queue_data["data"]["queue_length"] - 1
    assert not any(task["task_id"] == "CANCEL-TEST-001" for task in queue_data_after["data"]["tasks"])

    # Try to cancel a non-existent task
    cancel_nonexistent_response = client.delete("/api/v1/robotics/schedule/cancel/NONEXISTENT-001", headers=headers)
    assert cancel_nonexistent_response.status_code == 404


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


def test_robotics_emergency_response_protocols(client):
    headers = auth_headers(client)

    # Create an emergency event
    event_payload = {
        "event_type": "power_loss",
        "severity": "critical",
        "description": "Simulated critical power loss in zone ZONE-1",
        "triggered_by": "automated",
        "affected_systems": ["power_grid", "robotic_fleet"],
        "root_cause": "grid_failure",
        "metadata": {"source": "sensor_hub"}
    }
    event_response = client.post("/api/v1/robotics/emergency/events", json=event_payload, headers=headers)
    assert event_response.status_code == 200
    event_data = event_response.json()
    assert event_data["event_type"] == "power_loss"
    assert event_data["severity"] == "critical"
    event_id = event_data["event_id"]

    # List emergency events
    events_response = client.get("/api/v1/robotics/emergency/events", headers=headers)
    assert events_response.status_code == 200
    assert any(evt["event_id"] == event_id for evt in events_response.json())

    # Add an emergency response
    response_payload = {
        "action_type": "power_failover",
        "action_name": "Switch to generator backup",
        "description": "Activate backup generator and isolate grid load",
        "priority": 10,
        "affected_robots": ["ROVER-001"],
        "affected_zones": ["ZONE-1"],
        "affected_tasks": ["TASK-001"]
    }
    response_response = client.post(f"/api/v1/robotics/emergency/events/{event_id}/responses", json=response_payload, headers=headers)
    assert response_response.status_code == 200
    response_data = response_response.json()
    assert response_data["action_type"] == "power_failover"
    assert response_data["status"] == "pending"
    response_id = response_data["id"]

    # Complete the emergency response
    complete_payload = {"success": True, "error_message": None, "result_data": {"switched_to": "generator"}}
    complete_response = client.post(
        f"/api/v1/robotics/emergency/events/{event_id}/responses/{response_id}/complete",
        json=complete_payload,
        headers=headers,
    )
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["status"] == "completed"
    assert complete_data["success"] is True

    # Emergency status should now show resolved
    status_response = client.get(f"/api/v1/robotics/emergency/events/{event_id}/status", headers=headers)
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["event_id"] == event_id
    assert status_data["status"] in ("resolved", "active")

    # Create a backup power state transition
    power_payload = {
        "event_id": None,
        "is_active": True,
        "power_mode": "generator",
        "battery_level_percent": 85.0,
        "battery_capacity_wh": 5000.0,
        "estimated_runtime_hours": 6.5,
        "solar_generation_w": 0.0,
        "solar_max_capacity_w": 0.0,
        "current_load_w": 450.0,
        "max_load_w": 1000.0,
        "transition_reason": "grid_failure",
        "recovery_status": "in_progress",
        "recovery_eta_seconds": 3600
    }
    power_response = client.post("/api/v1/robotics/emergency/power-state", json=power_payload, headers=headers)
    assert power_response.status_code == 200
    power_data = power_response.json()
    assert power_data["power_mode"] == "generator"
    assert power_data["is_active"] is True

    # List backup power states
    power_list_response = client.get("/api/v1/robotics/emergency/power-state", headers=headers)
    assert power_list_response.status_code == 200
    assert isinstance(power_list_response.json(), list)

    # Manual override path
    override_payload = {
        "action_type": "system_reset",
        "reason": "Test manual override for emergency stop",
        "target_systems": ["robotic_fleet"],
        "force": True
    }
    override_response = client.post("/api/v1/robotics/emergency/manual-override", json=override_payload, headers=headers)
    assert override_response.status_code == 200
    override_data = override_response.json()
    assert override_data["action_type"] == "system_reset"
    assert override_data["status"] == "completed"

    headers = auth_headers(client)

    # Test real-time status endpoint
    status_response = client.get("/api/v1/robotics/monitoring/real-time-status", headers=headers)
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert "timestamp" in status_data
    assert "system_health" in status_data
    assert "fleet_status" in status_data
    assert "robot_health" in status_data
    assert "active_alerts" in status_data
    assert "performance_metrics" in status_data
    assert "last_updated" in status_data

    # Test alerts endpoint
    alerts_response = client.get("/api/v1/robotics/monitoring/alerts", headers=headers)
    assert alerts_response.status_code == 200
    alerts_data = alerts_response.json()
    assert isinstance(alerts_data, list)

    # Test monitoring dashboard endpoint
    dashboard_response = client.get("/api/v1/robotics/monitoring/dashboard", headers=headers)
    assert dashboard_response.status_code == 200
    dashboard_data = dashboard_response.json()
    assert "real_time_status" in dashboard_data
    assert "historical_data" in dashboard_data
    assert "alerts_summary" in dashboard_data
    assert "recommendations" in dashboard_data

    # Test recording health snapshot
    health_snapshot = {
        "robot_id": "ROVER-001",
        "status": "healthy",
        "battery_level": 85.5,
        "cpu_usage_percent": 45.2,
        "memory_usage_percent": 62.1,
        "temperature_c": 38.5,
        "uptime_seconds": 3600,
        "error_count": 0,
        "warning_count": 1,
        "position": {"x": 10.5, "y": 20.3, "z": 0.0},
        "current_task": "HARVEST-001",
        "firmware_version": "v1.2.3"
    }
    snapshot_response = client.post("/api/v1/robotics/monitoring/health-snapshot", json=health_snapshot, headers=headers)
    assert snapshot_response.status_code == 200
    snapshot_data = snapshot_response.json()
    assert snapshot_data["status"] == "success"
    assert snapshot_data["data"]["robot_id"] == "ROVER-001"

    # Test robot health history endpoint
    history_response = client.get("/api/v1/robotics/monitoring/robot-health/ROVER-001", headers=headers)
    assert history_response.status_code == 200
    history_data = history_response.json()
    assert isinstance(history_data, list)
    if history_data:
        assert history_data[0]["robot_id"] == "ROVER-001"


def test_robotics_data_synchronization_and_backup(client):
    headers = auth_headers(client)

    backup_payload = {
        "source": "biological_database",
        "record_count": 1580,
        "data_hash": "abc123hash",
        "storage_uri": "s3://aegis-backups/biological_db/backup-001",
        "status": "created",
        "integrity_verified": False,
        "verification_notes": "initial snapshot",
    }
    backup_response = client.post("/api/v1/robotics/sync/backups", json=backup_payload, headers=headers)
    assert backup_response.status_code == 200
    backup_data = backup_response.json()
    assert backup_data["source"] == "biological_database"
    assert backup_data["status"] == "created"
    assert backup_data["integrity_verified"] is False
    snapshot_id = backup_data["snapshot_id"]

    verify_payload = {
        "verification_hash": "abc123hash",
        "verification_notes": "hash verified",
        "status": "verified"
    }
    verified_response = client.post(f"/api/v1/robotics/sync/backups/{snapshot_id}/verify", json=verify_payload, headers=headers)
    assert verified_response.status_code == 200
    verified_data = verified_response.json()
    assert verified_data["integrity_verified"] is True
    assert verified_data["status"] == "verified"

    list_backups_response = client.get("/api/v1/robotics/sync/backups", headers=headers)
    assert list_backups_response.status_code == 200
    backups = list_backups_response.json()
    assert any(item["snapshot_id"] == snapshot_id for item in backups)

    sync_payload = {
        "source_system": "local_db",
        "target_system": "cloud_archive",
        "payload_hash": "syncpayloadhash",
    }
    sync_response = client.post("/api/v1/robotics/sync/jobs", json=sync_payload, headers=headers)
    assert sync_response.status_code == 200
    sync_data = sync_response.json()
    assert sync_data["source_system"] == "local_db"
    assert sync_data["target_system"] == "cloud_archive"
    assert sync_data["status"] == "pending"
    sync_id = sync_data["sync_id"]

    complete_payload = {
        "success": True,
        "result_summary": "Sync completed successfully",
        "payload_hash": "syncpayloadhash"
    }
    complete_response = client.post(f"/api/v1/robotics/sync/jobs/{sync_id}/complete", json=complete_payload, headers=headers)
    assert complete_response.status_code == 200
    complete_data = complete_response.json()
    assert complete_data["status"] == "completed"
    assert complete_data["attempt_count"] == 1

    list_jobs_response = client.get("/api/v1/robotics/sync/jobs", headers=headers)
    assert list_jobs_response.status_code == 200
    jobs = list_jobs_response.json()
    assert any(item["sync_id"] == sync_id for item in jobs)
