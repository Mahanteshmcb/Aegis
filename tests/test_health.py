"""
Aegis Backend - Health Endpoint Tests
"""

def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "healthy", "degraded", "unhealthy"]
    assert data["backend"] == "running"
    assert data["database"] in ["connected", "disconnected"]
    assert data["vryndara"] in ["connected", "disconnected", "fallback"]
    assert data["uptime_seconds"] >= 0
    assert data["timestamp"] is not None


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Aegis"
    assert data["status"] == "running"
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/v1/health"


def test_swagger_docs(client):
    """Test OpenAPI documentation endpoint."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "swagger" in response.text.lower()
