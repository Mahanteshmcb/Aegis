import pytest


def test_backend_health():
    # Placeholder test
    assert True

def auth_headers(client, email="user@example.com", password="testpass", tenant_name="Test Tenant"):
    # Register tenant
    client.post("/api/v1/tenants", json={"name": tenant_name})
    # Register user
    user_data = {
        "email": email,
        "password": password,
        "tenant_id": 1,
        "role": "admin"
    }
    client.post("/api/v1/auth/register", json=user_data)
    # Login user
    login_data = {"email": email, "password": password, "tenant_id": 1, "role": "admin"}
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_zone(client):
    headers = auth_headers(client)
    zone_data = {
        "name": "Zone 1",
        "description": "Test zone",
        "location": "Building A",
        "tenant_id": 1
    }
    response = client.post("/api/v1/zones", json=zone_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == zone_data["name"]
    assert data["tenant_id"] == zone_data["tenant_id"]

def test_create_and_get_sensor(client):
    headers = auth_headers(client)
    # Create a sensor
    sensor_data = {"tenant_id": 1, "type": "temperature", "location": "Room 101"}
    response = client.post("/api/v1/sensors", json=sensor_data, headers=headers)
    assert response.status_code == 200
    sensor = response.json()
    # Ingest sensor data
    ingest_data = {"sensor_id": sensor["id"], "value": 23.5, "unit": "C", "timestamp": "2026-03-22T10:00:00Z"}
    ingest_response = client.post("/api/v1/sensors/data", json=ingest_data, headers=headers)
    assert ingest_response.status_code == 200
    ingest_result = ingest_response.json()
    assert ingest_result["value"] == 23.5
    # Get sensor data
    get_response = client.get(f"/api/v1/sensors/{sensor['id']}/data", headers=headers)
    assert get_response.status_code == 200
    get_result = get_response.json()
    assert get_result["value"] == 23.5

def test_ai_orchestrator():

    # Placeholder test
    assert True

def test_unauthorized_access(client):
    # No token
    zone_data = {"name": "Zone 2", "description": "No auth", "location": "B", "tenant_id": 1}
    response = client.post("/api/v1/zones", json=zone_data)
    assert response.status_code == 401

def test_forbidden_access_wrong_role(client):
    # Register tenant and user as viewer
    client.post("/api/v1/tenants", json={"name": "Tenant Viewer"})
    user_data = {
        "email": "viewer@example.com",
        "password": "testpass",
        "tenant_id": 2,
        "role": "viewer"
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {"email": "viewer@example.com", "password": "testpass", "tenant_id": 2, "role": "viewer"}
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Try to create zone (admin only)
    zone_data = {"name": "Zone Viewer", "description": "Should fail", "location": "B", "tenant_id": 2}
    response = client.post("/api/v1/zones", json=zone_data, headers=headers)
    assert response.status_code in (401, 403)

def test_cross_tenant_isolation(client):
    # Tenant 1 admin
    headers1 = auth_headers(client, email="admin1@example.com", password="pass1", tenant_name="Tenant 1")
    # Tenant 2 admin
    client.post("/api/v1/tenants", json={"name": "Tenant 2"})
    user_data2 = {
        "email": "admin2@example.com",
        "password": "pass2",
        "tenant_id": 2,
        "role": "admin"
    }
    client.post("/api/v1/auth/register", json=user_data2)
    login_data2 = {"email": "admin2@example.com", "password": "pass2", "tenant_id": 2, "role": "admin"}
    resp2 = client.post("/api/v1/auth/login", json=login_data2)
    token2 = resp2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {token2}"}
    # Tenant 1 creates a zone
    zone_data1 = {"name": "Zone T1", "description": "T1", "location": "A", "tenant_id": 1}
    resp_zone1 = client.post("/api/v1/zones", json=zone_data1, headers=headers1)
    assert resp_zone1.status_code == 200
    zone_id = resp_zone1.json()["id"]
    # Tenant 2 tries to access tenant 1's zone (should fail or not found)
    resp_get = client.get(f"/api/v1/zones/{zone_id}", headers=headers2)
    assert resp_get.status_code in (401, 403, 404)

def test_token_refresh(client):
    # Register and login
    client.post("/api/v1/tenants", json={"name": "Tenant Refresh"})
    user_data = {
        "email": "refresh@example.com",
        "password": "testpass",
        "tenant_id": 3,
        "role": "admin"
    }
    client.post("/api/v1/auth/register", json=user_data)
    login_data = {"email": "refresh@example.com", "password": "testpass", "tenant_id": 3, "role": "admin"}
    resp = client.post("/api/v1/auth/login", json=login_data)
    assert resp.status_code == 200
    tokens = resp.json()
    refresh_token = tokens["refresh_token"]
    # Use refresh token
    resp_refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_refresh.status_code == 200
    new_tokens = resp_refresh.json()
    assert "access_token" in new_tokens