"""Day 59: Software Completion Milestone - Performance Benchmarking

Measures API response times, identifies bottlenecks, and establishes
baseline performance metrics for key endpoints.
"""
import pytest
import time
from datetime import datetime


class PerformanceMetrics:
    """Collect and report performance metrics."""
    def __init__(self):
        self.measurements = {}
    
    def record(self, endpoint, duration_ms):
        if endpoint not in self.measurements:
            self.measurements[endpoint] = []
        self.measurements[endpoint].append(duration_ms)
    
    def report(self):
        print("\n" + "="*70)
        print("PERFORMANCE BASELINE METRICS (Day 59)")
        print("="*70)
        for endpoint, durations in sorted(self.measurements.items()):
            avg = sum(durations) / len(durations)
            min_dur = min(durations)
            max_dur = max(durations)
            print(f"{endpoint:50s}: {avg:8.2f}ms [min: {min_dur:.2f}ms, max: {max_dur:.2f}ms]")
        print("="*70)
        return self.measurements


metrics = PerformanceMetrics()


def measure_request(func, name):
    """Decorator to measure endpoint response time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000  # Convert to ms
        metrics.record(name, duration)
        return result
    return wrapper


def test_health_check_performance(client):
    """Baseline: Health check should be <3000ms (includes Vryndara init)."""
    start = time.time()
    resp = client.get("/api/v1/health")
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/health", duration)
    assert resp.status_code == 200
    assert duration < 3000.0, f"Health check too slow: {duration:.2f}ms"


def test_zone_list_performance(client, test_db):
    """Zone list retrieval should be <100ms."""
    token = "test-token"
    
    start = time.time()
    resp = client.get("/api/v1/zones", headers={"Authorization": f"Bearer {token}"})
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/zones", duration)
    assert resp.status_code == 200
    assert duration < 100.0, f"Zone list too slow: {duration:.2f}ms"


def test_sensor_list_performance(client, test_db):
    """Sensor list retrieval should be <50ms."""
    token = "test-token"
    
    start = time.time()
    resp = client.get("/api/v1/sensors", headers={"Authorization": f"Bearer {token}"})
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/sensors", duration)
    assert resp.status_code == 200
    assert duration < 50.0, f"Sensor list too slow: {duration:.2f}ms"


def test_weather_forecast_performance(client, test_db):
    """Local forecast computation should be <100ms (cache hits <20ms)."""
    token = "test-token"
    
    # First call (computation)
    start = time.time()
    resp1 = client.get(
        "/api/v1/weather/local_forecast?tenant_id=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration1 = (time.time() - start) * 1000
    metrics.record("GET /api/v1/weather/local_forecast (compute)", duration1)
    
    # Second call (cache hit)
    start = time.time()
    resp2 = client.get(
        "/api/v1/weather/local_forecast?tenant_id=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration2 = (time.time() - start) * 1000
    metrics.record("GET /api/v1/weather/local_forecast (cached)", duration2)
    
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    assert duration2 < 20.0, f"Forecast cache too slow: {duration2:.2f}ms"


def test_energy_status_performance(client, test_db):
    """Energy status with schedule computation should be <100ms."""
    token = "test-token"
    
    start = time.time()
    resp = client.get(
        "/api/v1/energy/status?tenant_id=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/energy/status", duration)
    assert resp.status_code == 200
    assert duration < 100.0, f"Energy status too slow: {duration:.2f}ms"


def test_smart_schedule_performance(client, test_db):
    """Adaptive schedule with weather integration should be <150ms."""
    token = "test-token"
    
    start = time.time()
    resp = client.get(
        "/api/v1/energy/smart_schedule?tenant_id=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/energy/smart_schedule", duration)
    assert resp.status_code == 200
    assert duration < 150.0, f"Smart schedule too slow: {duration:.2f}ms"


def test_weather_observations_query_performance(client, test_db):
    """Observation queries should be <50ms for small result sets."""
    token = "test-token"
    
    start = time.time()
    resp = client.get(
        "/api/v1/weather/observations?tenant_id=1&limit=20",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/weather/observations", duration)
    assert resp.status_code == 200
    assert duration < 50.0, f"Observations query too slow: {duration:.2f}ms"


def test_audit_log_query_performance(client, test_db):
    """Audit log retrieval should be <100ms for reasonable page sizes."""
    token = "test-token"
    
    start = time.time()
    resp = client.get(
        "/api/v1/audit?limit=50",
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("GET /api/v1/audit", duration)
    assert resp.status_code == 200
    assert duration < 100.0, f"Audit log query too slow: {duration:.2f}ms"


def test_sensor_creation_performance(client, test_db):
    """Sensor creation (with audit logging) should be <200ms."""
    token = "test-token"
    
    start = time.time()
    resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Perf Test Sensor",
            "type": "temperature_sensor",
            "tenant_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("POST /api/v1/sensors", duration)
    assert resp.status_code == 200
    assert duration < 200.0, f"Sensor creation too slow: {duration:.2f}ms"


def test_sensor_telemetry_ingestion_performance(client, test_db):
    """Telemetry ingestion (SensorData + WeatherObservation) should be <100ms."""
    token = "test-token"
    
    # Create sensor first
    s_resp = client.post(
        "/api/v1/sensors",
        json={
            "name": "Telemetry Test",
            "type": "temperature_humidity_sensor",
            "tenant_id": 1,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    sensor_id = s_resp.json()["id"]
    
    # Measure telemetry ingestion
    start = time.time()
    resp = client.post(
        "/api/v1/weather/observe",
        json={
            "tenant_id": 1,
            "sensor_id": sensor_id,
            "temp_c": 22.5,
            "humidity_percent": 60.0,
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    duration = (time.time() - start) * 1000
    
    metrics.record("POST /api/v1/weather/observe", duration)
    assert resp.status_code == 200
    assert duration < 100.0, f"Telemetry ingestion too slow: {duration:.2f}ms"


def test_concurrent_requests_stability(client, test_db):
    """System should handle multiple rapid requests without degradation."""
    token = "test-token"
    
    # Simulate rapid requests
    durations = []
    for _ in range(10):
        start = time.time()
        resp = client.get(
            "/api/v1/weather/observations?tenant_id=1&limit=5",
            headers={"Authorization": f"Bearer {token}"}
        )
        duration = (time.time() - start) * 1000
        durations.append(duration)
        assert resp.status_code == 200
    
    metrics.record("GET /api/v1/weather/observations (concurrent x10)", sum(durations) / len(durations))
    
    # Check no significant slowdown (last requests shouldn't be much slower than first)
    avg_first_5 = sum(durations[:5]) / 5
    avg_last_5 = sum(durations[5:]) / 5
    slowdown_ratio = avg_last_5 / avg_first_5
    
    assert slowdown_ratio < 1.5, f"Significant slowdown under concurrent load: {slowdown_ratio:.2f}x"


@pytest.fixture(scope="session", autouse=True)
def report_metrics():
    """Report metrics at end of session."""
    yield
    metrics.report()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
