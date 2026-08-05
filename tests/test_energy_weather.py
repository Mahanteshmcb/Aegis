import pytest
from jose import jwt

from backend import models_db
from backend.config import settings


def test_weather_observation_forecast_recommendations(client):
    observation = {
        "tenant_id": 1,
        "zone_id": 1,
        "temp_c": 17.0,
        "humidity_percent": 72.5,
        "wind_m_s": 5.4,
        "precip_mm": 1.8,
        "pressure_hpa": 1012.4,
        "timestamp": "2026-05-23T10:00:00"
    }

    response = client.post("/api/v1/weather/observe", json=observation)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert isinstance(response.json()["id"], int)

    forecast_response = client.get("/api/v1/weather/local_forecast?tenant_id=1&zone_id=1")
    assert forecast_response.status_code == 200
    forecast_data = forecast_response.json()
    assert forecast_data["ok"] is True
    assert isinstance(forecast_data["forecast"], list)
    assert len(forecast_data["forecast"]) >= 1

    rec_response = client.get("/api/v1/weather/maintenance/recommendations?tenant_id=1&zone_id=1")
    assert rec_response.status_code == 200
    rec_data = rec_response.json()
    assert rec_data["ok"] is True
    assert isinstance(rec_data["recommendations"], list)


def test_energy_policy_persistence(client):
    policy_payload = {
        "charge_threshold": 0.7,
        "discharge_threshold": 0.25,
        "max_charge_rate_kw": 2.5,
    }

    post_response = client.post("/api/v1/energy/policy", json=policy_payload)
    assert post_response.status_code == 200
    post_data = post_response.json()
    assert post_data["ok"] is True
    assert post_data["policy"]["charge_threshold"] == pytest.approx(0.7)

    get_response = client.get("/api/v1/energy/policy")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["charge_threshold"] == pytest.approx(0.7)
    assert get_data["discharge_threshold"] == pytest.approx(0.25)
    assert get_data["max_charge_rate_kw"] == pytest.approx(2.5)


def test_energy_status_uses_weather_forecast_cache(client):
    # Ensure forecast cache exists before checking energy status
    response = client.get("/api/v1/weather/local_forecast")
    assert response.status_code == 200
    assert response.json()["ok"] is True

    status_response = client.get("/api/v1/energy/status")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert isinstance(status_data["balance_kwh"], float)
    assert isinstance(status_data["schedule"], list)
    assert all("hour" in item and "action" in item for item in status_data["schedule"])


def test_sensor_telemetry_ingestion_updates_weather_observations(client, test_db):
    db_session = test_db()
    tenant = models_db.Tenant(id=1, name="Test Tenant")
    zone = models_db.Zone(id=1, name="Greenhouse Dome", tenant_id=1)
    user = models_db.User(id=1, tenant_id=1, email="test-user@example.com", hashed_password="test", role="admin")

    db_session.add_all([tenant, zone, user])
    db_session.commit()

    auth_token = jwt.encode({"sub": str(user.id), "tenant_id": tenant.id}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    headers = {"Authorization": f"Bearer {auth_token}"}

    sensor_payload = {
        "tenant_id": 1,
        "zone_id": 1,
        "name": "Aegis-Air-Temp-01",
        "type": "temperature",
        "location": "Greenhouse Dome"
    }
    create_resp = client.post("/api/v1/sensors", headers=headers, json=sensor_payload)
    assert create_resp.status_code == 200
    sensor = create_resp.json()
    assert sensor["type"] == "temperature"

    telemetry = {
        "sensor_id": sensor["id"],
        "value": 22.4,
        "unit": "°C",
        "timestamp": "2026-05-23 12:30:00"
    }
    ingest_resp = client.post("/api/v1/sensors/data", headers=headers, json=telemetry)
    assert ingest_resp.status_code == 200
    ingest_data = ingest_resp.json()
    assert ingest_data["status"] == "online"
    assert ingest_data["zone_id"] == 1

    obs_resp = client.get("/api/v1/weather/observations?tenant_id=1&zone_id=1")
    assert obs_resp.status_code == 200
    obs_data = obs_resp.json()
    assert obs_data["ok"] is True
    assert isinstance(obs_data["observations"], list)
    assert any(obs["sensor_id"] == sensor["id"] for obs in obs_data["observations"])

    # Validate local forecast and energy status reflect the ingested observation
    forecast_response = client.get("/api/v1/weather/local_forecast?tenant_id=1&zone_id=1")
    assert forecast_response.status_code == 200
    assert forecast_response.json()["ok"] is True

    energy_response = client.get("/api/v1/energy/status?tenant_id=1")
    assert energy_response.status_code == 200
    energy_data = energy_response.json()
    assert isinstance(energy_data["balance_kwh"], float)
    assert isinstance(energy_data["schedule"], list)
    assert all("hour" in item and "action" in item for item in energy_data["schedule"])


def test_energy_overview_returns_grid_summary(client):
    response = client.get("/api/v1/energy/overview")
    assert response.status_code == 200
    overview = response.json()
    assert isinstance(overview["total_generation_kwh"], float)
    assert isinstance(overview["total_consumption_kwh"], float)
    assert isinstance(overview["net_balance_kwh"], float)
    assert isinstance(overview["battery_soc"], float)
    assert isinstance(overview["battery_capacity_kwh"], float)
    assert isinstance(overview["solar_asset_count"], int)
    assert isinstance(overview["battery_asset_count"], int)
    assert "schedule" in overview and isinstance(overview["schedule"], list)
    assert "metrics" in overview and isinstance(overview["metrics"], dict)
    assert overview["grid_asset_count"] >= 0


def test_energy_overview_includes_multiple_sources(client):
    response = client.get("/api/v1/energy/overview")
    assert response.status_code == 200
    overview = response.json()

    assert isinstance(overview["source_counts"], dict)
    assert isinstance(overview["source_breakdown"], dict)
    assert overview["source_counts"].get("solar", 0) >= 0
    assert overview["source_counts"].get("wind", 0) >= 0
    assert overview["source_counts"].get("hydro", 0) >= 0
    assert overview["source_counts"].get("grid", 0) >= 0
    assert overview["source_breakdown"].get("solar", 0.0) >= 0.0
    assert overview["source_breakdown"].get("wind", 0.0) >= 0.0
    assert overview["source_breakdown"].get("hydro", 0.0) >= 0.0
    assert overview["source_breakdown"].get("grid", 0.0) >= 0.0
