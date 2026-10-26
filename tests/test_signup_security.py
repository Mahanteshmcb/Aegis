def test_public_signup_forces_viewer_role(client):
    tenant_response = client.post("/api/v1/tenants", json={"name": "Signup Tenant"})
    assert tenant_response.status_code == 200

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "self-registered@example.com",
            "password": "securepass123",
            "tenant_id": tenant_response.json()["id"],
            "role": "admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["role"] == "viewer"


def test_public_signup_is_disabled_in_production(client, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "environment", "prod")
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": "production-signup@example.com",
            "password": "securepass123",
            "tenant_id": 1,
        },
    )

    assert response.status_code == 403