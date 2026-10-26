"""Day 61: Estate dashboard API tests."""

from passlib.hash import bcrypt

import pytest

from backend.models_db import Tenant, User


@pytest.fixture
def token(client):
    return "test-token"


def test_login(client, test_db):
    db = test_db()
    try:
        tenant = Tenant(name="Estate login test tenant")
        db.add(tenant)
        db.flush()
        db.add(
            User(
                tenant_id=tenant.id,
                email="admin@aegis.com",
                hashed_password=bcrypt.hash("admin1234"),
                role="admin",
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@aegis.com", "password": "admin1234"},
    )
    assert response.status_code == 200, response.text
    assert response.json().get("access_token")


def test_estate_status(client, token):
    response = client.get(
        "/api/v1/estate/status",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("systems_online") is not None
    assert data.get("overall_health") is not None
    assert data.get("climate") is not None


def test_system_data_climate(client, token):
    response = client.get(
        "/api/v1/systems/climate/data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("system_id") == "climate"
    assert data.get("status") is not None


def test_system_data_energy(client, token):
    response = client.get(
        "/api/v1/systems/energy/data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("system_id") == "energy"
    assert data.get("status") is not None


def test_estate_timeline(client, token):
    response = client.get(
        "/api/v1/estate/timeline",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": 1, "page_size": 10},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("total_events") is not None
    assert data.get("page") == 1
    assert data.get("total_pages") is not None


def test_all_systems(client, token):
    response = client.get(
        "/api/v1/systems",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data.get("total_systems") is not None
    assert len(data.get("systems", [])) > 0


def test_timeline_filters(client, token):
    response = client.get(
        "/api/v1/estate/timeline",
        headers={"Authorization": f"Bearer {token}"},
        params={"system": "climate", "severity": "warning"},
    )
    assert response.status_code == 200, response.text
    assert response.json().get("total_events") is not None
