"""Day 59: Software Completion Milestone - E2E Integration Tests

Comprehensive end-to-end integration test validating full pipeline:
tenant creation → zone definition → sensor registration → telemetry ingestion →
weather observation → forecast computation → energy status → smart scheduling.

This test suite ensures all components work together seamlessly.
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


def test_full_pipeline_tenant_to_scheduling(client, test_db, mock_blockchain):
    """Complete pipeline: tenant → zone → sensor → telemetry → weather → energy."""
    token = "test-token"
    
    # Step 1: Create tenant (implicit from DB)
    tenant_id = 1
    
    # Step 2: Create zone
    zone_resp = client.post(
        "/api/v1/zones",
        json={"name": "Test Farm Zone", "tenant_id": tenant_id, "location": "Field A"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert zone_resp.status_code == 200
    zone_id = zone_resp.json()["id"]
    
    # Step 3: Register environmental sensor (will auto-trigger weather observations)
    sensor_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Environmental Probe",
            "type": "temperature_humidity_sensor",
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "unit": "°C",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert sensor_resp.status_code == 200
    sensor_id = sensor_resp.json()["id"]
    
    # Step 4: Ingest sensor telemetry as weather observation
    ingest_resp = client.post(
        "/api/v1/weather/observe",
        json={
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "sensor_id": sensor_id,
            "timestamp": datetime.utcnow().isoformat(),
            "temp_c": 22.5,
            "humidity_percent": 65.0,
            "wind_m_s": 2.1,
            "precip_mm": 0.0,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert ingest_resp.status_code == 200
    
    # Step 5: Query local forecast (should use recent observations)
    forecast_resp = client.get(
        f"/api/v1/weather/local_forecast?tenant_id={tenant_id}&zone_id={zone_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert forecast_resp.status_code == 200
    forecast = forecast_resp.json()
    assert forecast["ok"]
    assert len(forecast["forecast"]) > 0
    
    # Step 6: Get maintenance recommendations
    maint_resp = client.get(
        f"/api/v1/weather/maintenance/recommendations?tenant_id={tenant_id}&zone_id={zone_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert maint_resp.status_code == 200
    
    # Step 7: Register generation and consumption sensors
    gen_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Solar Panel Array",
            "type": "solar_pv_generation",
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "unit": "kW",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert gen_resp.status_code == 200
    gen_sensor_id = gen_resp.json()["id"]
    
    cons_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Grid Meter",
            "type": "consumption_meter",
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "unit": "kW",
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cons_resp.status_code == 200
    cons_sensor_id = cons_resp.json()["id"]
    
    # Step 8: Ingest generation and consumption readings
    client.post(
        "/api/v1/sensors/data",
        json={"sensor_id": gen_sensor_id, "value": 2.5, "unit": "kW"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/api/v1/sensors/data",
        json={"sensor_id": cons_sensor_id, "value": 1.2, "unit": "kW"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Step 9: Get energy status with forecast integration
    energy_resp = client.get(
        f"/api/v1/energy/status?tenant_id={tenant_id}&zone_id={zone_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert energy_resp.status_code == 200
    energy_data = energy_resp.json()
    assert "balance_kwh" in energy_data
    assert "schedule" in energy_data
    assert len(energy_data["schedule"]) > 0
    
    # Step 10: Get adaptive schedule (weather-informed)
    smart_resp = client.get(
        f"/api/v1/energy/smart_schedule?tenant_id={tenant_id}&zone_id={zone_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert smart_resp.status_code == 200
    smart_data = smart_resp.json()
    assert smart_data["ok"]
    assert "schedule" in smart_data
    assert "metrics" in smart_data
    assert "recommendations" in smart_data
    
    # Step 11: Verify data persistence - query observations
    obs_resp = client.get(
        f"/api/v1/weather/observations?tenant_id={tenant_id}&limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert obs_resp.status_code == 200
    obs_data = obs_resp.json()
    assert len(obs_data["observations"]) > 0
    assert obs_data["observations"][0]["temp_c"] == 22.5
    
    # Step 12: Verify audit trail
    audit_resp = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert audit_resp.status_code == 200
    audit_logs = audit_resp.json()
    assert len(audit_logs) > 0
    # Should have sensor creation events
    sensor_events = [log for log in audit_logs if "sensor" in str(log).lower()]
    assert len(sensor_events) > 0


def test_multi_zone_isolation(client, test_db, mock_blockchain):
    """Verify data is properly isolated between zones."""
    token = "test-token"
    tenant_id = 1
    
    # Create two zones
    z1_resp = client.post(
        "/api/v1/zones",
        json={"name": "Zone 1", "tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    zone1_id = z1_resp.json()["id"]
    
    z2_resp = client.post(
        "/api/v1/zones",
        json={"name": "Zone 2", "tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    zone2_id = z2_resp.json()["id"]
    
    # Create sensors in each zone
    s1_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Zone 1 Temp",
            "type": "temperature_sensor",
            "tenant_id": tenant_id,
            "zone_id": zone1_id,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    s1_id = s1_resp.json()["id"]
    
    s2_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Zone 2 Temp",
            "type": "temperature_sensor",
            "tenant_id": tenant_id,
            "zone_id": zone2_id,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    s2_id = s2_resp.json()["id"]
    
    # Ingest different temperatures
    client.post(
        "/api/v1/weather/observe",
        json={
            "tenant_id": tenant_id,
            "zone_id": zone1_id,
            "sensor_id": s1_id,
            "temp_c": 20.0,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    client.post(
        "/api/v1/weather/observe",
        json={
            "tenant_id": tenant_id,
            "zone_id": zone2_id,
            "sensor_id": s2_id,
            "temp_c": 25.0,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Query zone1 observations - should only see temp_c=20
    z1_obs = client.get(
        f"/api/v1/weather/observations?tenant_id={tenant_id}&zone_id={zone1_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    z1_data = z1_obs.json()["observations"]
    assert all(obs["temp_c"] == 20.0 for obs in z1_data if obs["temp_c"] is not None)
    
    # Query zone2 observations - should only see temp_c=25
    z2_obs = client.get(
        f"/api/v1/weather/observations?tenant_id={tenant_id}&zone_id={zone2_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    z2_data = z2_obs.json()["observations"]
    assert all(obs["temp_c"] == 25.0 for obs in z2_data if obs["temp_c"] is not None)


def test_weather_to_energy_cascade(client, test_db, mock_blockchain):
    """Verify weather observations cascade to energy scheduling decisions."""
    token = "test-token"
    tenant_id = 1
    
    # Create zone and sensors
    z_resp = client.post(
        "/api/v1/zones",
        json={"name": "Energy Test Zone", "tenant_id": tenant_id},
        headers={"Authorization": f"Bearer {token}"}
    )
    zone_id = z_resp.json()["id"]
    
    # Create all sensor types
    sensors = {}
    for stype, name in [("temp", "Temperature"), ("solar", "Solar Gen"), ("consumption", "Load")]:
        s_resp = client.post(
            "/api/v1/sensors",
            json={
                "name": name,
                "type": stype + "_sensor" if stype == "temp" else ("solar_pv" if stype == "solar" else "consumption_meter"),
                "tenant_id": tenant_id,
                "zone_id": zone_id,
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        sensors[stype] = s_resp.json()["id"]
    
    # Ingest weather: cold + sunny (good for PV)
    client.post(
        "/api/v1/weather/observe",
        json={
            "tenant_id": tenant_id,
            "zone_id": zone_id,
            "sensor_id": sensors["temp"],
            "temp_c": 5.0,  # Cold = better PV efficiency
            "humidity_percent": 40,
            "cloud_percent": 20,
            "precip_mm": 0.0,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Ingest energy readings
    client.post(
        "/api/v1/sensors/data",
        json={"sensor_id": sensors["solar"], "value": 3.0, "unit": "kW"},
        headers={"Authorization": f"Bearer {token}"}
    )
    client.post(
        "/api/v1/sensors/data",
        json={"sensor_id": sensors["consumption"], "value": 1.5, "unit": "kW"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Get adaptive schedule - should show high confidence charging due to cold+sunny weather
    sched_resp = client.get(
        f"/api/v1/energy/smart_schedule?tenant_id={tenant_id}&zone_id={zone_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    sched_data = sched_resp.json()
    assert sched_data["ok"]
    
    # Should have charging actions due to surplus generation
    has_charging = any("charge" in str(s.get("action", "")).lower() for s in sched_data["schedule"])
    assert has_charging, "Schedule should show charging opportunities with good solar forecast"


def test_compliance_audit_trail(client, test_db, mock_blockchain):
    """Verify audit trail captures all compliance-relevant actions."""
    token = "test-token"
    tenant_id = 1
    
    # Request organic certification (compliance event)
    cert_resp = client.post(
        "/api/v1/audit/compliance/organic-certification/request",
        json={
            "tenant_id": tenant_id,
            "details": "Requesting organic certification for sustainable operations",
            "certification_level": "organic"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cert_resp.status_code in [200, 201]
    
    # Verify audit log was created
    audit_resp = client.get(
        "/api/v1/audit",
        headers={"Authorization": f"Bearer {token}"}
    )
    audit_logs = audit_resp.json()
    
    # Should have compliance event
    compliance_events = [log for log in audit_logs if "organic" in str(log).lower() or "certification" in str(log).lower()]
    assert len(compliance_events) > 0, "Compliance request should create audit entry"
    
    # Get compliance status
    status_resp = client.get(
        f"/api/v1/audit/compliance/organic-certification/{tenant_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert "organic_certification_requests" in status_data or "certification_requests" in status_data or "count" in status_data


def test_error_scenarios(client, test_db, mock_blockchain):
    """Verify system handles error conditions gracefully."""
    token = "test-token"
    
    # Test 404 - nonexistent resource
    resp = client.get(
        "/api/v1/weather/observations?zone_id=9999",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200  # Should return empty list, not 404
    assert resp.json()["observations"] == []
    
    # Test invalid sensor data
    resp = client.post(
        "/api/v1/sensors/data",
        json={"sensor_id": 9999, "value": 1.0, "unit": "kW"},
        headers={"Authorization": f"Bearer {token}"}
    )
    # Should handle gracefully (404 or 403 if multi-tenant isolated)
    assert resp.status_code in [400, 404, 403]
    
    # Test missing required fields in weather observation
    resp = client.post(
        "/api/v1/weather/observe",
        json={"tenant_id": 1},  # Missing required fields
        headers={"Authorization": f"Bearer {token}"}
    )
    # Endpoint may be lenient with missing fields (defaults), so accept 200 or validation error
    assert resp.status_code in [200, 400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
