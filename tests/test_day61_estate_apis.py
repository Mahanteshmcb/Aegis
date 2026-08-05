"""
Day 61 Testing: Estate Dashboard APIs
Run this to verify all endpoints work correctly
"""

import requests
import json
import pytest
from datetime import datetime

BASE_URL = "http://127.0.0.1:8001"


@pytest.fixture(scope="function")
def token():
    """Get auth token for testing"""
    login_data = {
        "email": "admin@aegis.com",
        "password": "admin1234"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


def test_login():
    """Get auth token for testing"""
    login_data = {
        "email": "admin@aegis.com",
        "password": "admin1234"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert data.get("access_token")


def test_estate_status(token):
    """Test: GET /api/v1/estate/status"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/estate/status", headers=headers)
    
    print("\n" + "="*60)
    print("TEST 1: GET /api/v1/estate/status")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('systems_online') is not None
    assert data.get('overall_health') is not None
    assert data.get('climate') is not None
    print("✅ All estate status fields present")


def test_system_data_climate(token):
    """Test: GET /api/v1/systems/climate/data"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/systems/climate/data", headers=headers)
    
    print("\n" + "="*60)
    print("TEST 2: GET /api/v1/systems/climate/data")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('system_id') == 'climate'
    assert data.get('status') is not None
    print("✅ Climate system data valid")


def test_system_data_energy(token):
    """Test: GET /api/v1/systems/energy/data"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/systems/energy/data", headers=headers)
    
    print("\n" + "="*60)
    print("TEST 3: GET /api/v1/systems/energy/data")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('system_id') == 'energy'
    assert data.get('status') is not None
    print("✅ Energy system data valid")


def test_estate_timeline(token):
    """Test: GET /api/v1/estate/timeline"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": 1, "page_size": 10}
    response = requests.get(f"{BASE_URL}/api/v1/estate/timeline", headers=headers, params=params)
    
    print("\n" + "="*60)
    print("TEST 4: GET /api/v1/estate/timeline")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('total_events') is not None
    assert data.get('page') is not None
    assert data.get('total_pages') is not None
    print("✅ Timeline data valid")


def test_all_systems(token):
    """Test: GET /api/v1/systems"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/systems", headers=headers)
    
    print("\n" + "="*60)
    print("TEST 5: GET /api/v1/systems")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('total_systems') is not None
    assert len(data.get('systems', [])) > 0
    print("✅ Systems list valid")


def test_timeline_filters(token):
    """Test: Timeline with filters"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"system": "climate", "severity": "warning"}
    response = requests.get(f"{BASE_URL}/api/v1/estate/timeline", headers=headers, params=params)
    
    print("\n" + "="*60)
    print("TEST 6: GET /api/v1/estate/timeline with filters")
    print("="*60)
    
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data.get('total_events') is not None
    print("✅ Timeline filters work")
