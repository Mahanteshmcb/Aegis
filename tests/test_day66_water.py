import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import SessionLocal, engine
from backend.models_db import Base
from backend.models.water import (
    WaterCollectionSystem,
    WaterPurificationUnit,
    IrrigationSystem,
    WaterQualityReading,
    WaterRecyclingLoop,
)
from tests.conftest import create_tenant, create_operator_user, get_token_for_user

client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield SessionLocal()
    Base.metadata.drop_all(bind=engine)


def test_water_collection_system_creation_and_retrieval(test_db):
    """Test creating and retrieving water collection systems."""
    # Setup: Create tenant and user
    tenant = create_tenant(test_db, "water_test_tenant_001")
    user = create_operator_user(test_db, "water_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # Test creating a water collection system
    collection_payload = {
        "system_name": "Main Rainwater Tank",
        "collection_type": "rainfall",
        "capacity_liters": 5000.0,
        "location": "North Roof",
    }
    response = client.post(
        "/api/v1/water/collection",
        json=collection_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    system = response.json()
    assert system["system_name"] == "Main Rainwater Tank"
    assert system["collection_type"] == "rainfall"
    assert system["capacity_liters"] == 5000.0
    assert system["current_volume_liters"] == 0.0

    # Test retrieving water collection systems
    response = client.get(
        "/api/v1/water/collection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    systems = response.json()
    assert len(systems) == 1
    assert systems[0]["system_name"] == "Main Rainwater Tank"


def test_water_purification_unit_creation_and_retrieval(test_db):
    """Test creating and retrieving water purification units."""
    # Setup
    tenant = create_tenant(test_db, "purification_test_tenant_001")
    user = create_operator_user(test_db, "purification_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # Test creating a purification unit
    purification_payload = {
        "unit_name": "Primary Reverse Osmosis Unit",
        "purification_type": "reverse_osmosis",
        "flow_rate_lpm": 100.0,
        "efficiency_percent": 95.5,
    }
    response = client.post(
        "/api/v1/water/purification",
        json=purification_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    unit = response.json()
    assert unit["unit_name"] == "Primary Reverse Osmosis Unit"
    assert unit["purification_type"] == "reverse_osmosis"
    assert unit["status"] == "ready"
    assert unit["efficiency_percent"] == 95.5

    # Test retrieving purification units
    response = client.get(
        "/api/v1/water/purification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    units = response.json()
    assert len(units) == 1
    assert units[0]["unit_name"] == "Primary Reverse Osmosis Unit"


def test_irrigation_system_creation_and_optimization(test_db):
    """Test creating and managing irrigation systems with optimization."""
    # Setup
    tenant = create_tenant(test_db, "irrigation_test_tenant_001")
    user = create_operator_user(test_db, "irrigation_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # Test creating an irrigation system
    irrigation_payload = {
        "system_name": "Drip Irrigation Zone A",
        "irrigation_type": "drip",
        "zone_id": None,
        "scheduled_frequency_minutes": 120,
        "water_per_cycle_liters": 50.0,
        "soil_moisture_target_percent": 65.0,
    }
    response = client.post(
        "/api/v1/water/irrigation",
        json=irrigation_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    system = response.json()
    assert system["system_name"] == "Drip Irrigation Zone A"
    assert system["irrigation_type"] == "drip"
    assert system["status"] == "idle"
    assert system["optimization_enabled"] is True
    assert system["water_per_cycle_liters"] == 50.0

    # Test retrieving irrigation systems
    response = client.get(
        "/api/v1/water/irrigation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    systems = response.json()
    assert len(systems) == 1
    assert systems[0]["system_name"] == "Drip Irrigation Zone A"


def test_water_quality_monitoring_and_contamination_detection(test_db):
    """Test recording and analyzing water quality readings with contamination detection."""
    # Setup
    tenant = create_tenant(test_db, "quality_test_tenant_001")
    user = create_operator_user(test_db, "quality_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # Test recording a good quality reading
    quality_payload = {
        "reading_location": "collection",
        "ph_level": 7.2,
        "turbidity_ntu": 0.3,
        "total_dissolved_solids_ppm": 150.0,
        "chlorine_ppm": 0.0,
        "dissolved_oxygen_ppm": 8.5,
        "temperature_celsius": 22.0,
        "bacterial_count_cfu_ml": 10.0,
        "contamination_detected": False,
    }
    response = client.post(
        "/api/v1/water/quality",
        json=quality_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    reading = response.json()
    assert reading["reading_location"] == "collection"
    assert reading["ph_level"] == 7.2
    assert reading["overall_quality_status"] == "good"
    assert reading["contamination_detected"] is False

    # Test recording a contaminated reading
    contaminated_payload = {
        "reading_location": "purified",
        "ph_level": 5.0,
        "turbidity_ntu": 8.5,
        "total_dissolved_solids_ppm": 500.0,
        "chlorine_ppm": 1.5,
        "dissolved_oxygen_ppm": 4.0,
        "temperature_celsius": 25.0,
        "bacterial_count_cfu_ml": 500.0,
        "contamination_detected": True,
        "contamination_type": "bacterial",
        "contaminant_level_ppm": 2.5,
    }
    response = client.post(
        "/api/v1/water/quality",
        json=contaminated_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    contaminated_reading = response.json()
    assert contaminated_reading["overall_quality_status"] == "contaminated"
    assert contaminated_reading["contamination_detected"] is True
    assert contaminated_reading["contamination_type"] == "bacterial"

    # Test retrieving quality readings by location
    response = client.get(
        "/api/v1/water/quality/collection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    readings = response.json()
    assert len(readings) == 1
    assert readings[0]["overall_quality_status"] == "good"

    response = client.get(
        "/api/v1/water/quality/purified",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    contaminated_readings = response.json()
    assert len(contaminated_readings) == 1
    assert contaminated_readings[0]["overall_quality_status"] == "contaminated"


def test_water_recycling_loop_management(test_db):
    """Test creating and managing water recycling loops."""
    # Setup
    tenant = create_tenant(test_db, "recycling_test_tenant_001")
    user = create_operator_user(test_db, "recycling_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # Test creating a greywater recycling loop
    recycling_payload = {
        "loop_name": "Greywater Reuse Loop",
        "loop_type": "greywater_reuse",
        "source_system": "Bathroom Drainage",
        "destination_system": "Irrigation System",
    }
    response = client.post(
        "/api/v1/water/recycling",
        json=recycling_payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    loop = response.json()
    assert loop["loop_name"] == "Greywater Reuse Loop"
    assert loop["loop_type"] == "greywater_reuse"
    assert loop["active"] is True
    assert loop["daily_recycled_liters"] == 0.0
    assert loop["total_recycled_liters"] == 0.0
    assert loop["efficiency_percent"] == 85.0

    # Test retrieving recycling loops
    response = client.get(
        "/api/v1/water/recycling",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    loops = response.json()
    assert len(loops) == 1
    assert loops[0]["loop_name"] == "Greywater Reuse Loop"


def test_complete_water_management_workflow(test_db):
    """Integration test for complete water management system workflow."""
    # Setup
    tenant = create_tenant(test_db, "workflow_test_tenant_001")
    user = create_operator_user(test_db, "workflow_operator@test.com", tenant.id)
    token = get_token_for_user(user)

    # 1. Create water collection system
    collection_response = client.post(
        "/api/v1/water/collection",
        json={
            "system_name": "Primary Collection Tank",
            "collection_type": "rainfall",
            "capacity_liters": 10000.0,
            "location": "Main Building Roof",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert collection_response.status_code == 200

    # 2. Create purification unit
    purification_response = client.post(
        "/api/v1/water/purification",
        json={
            "unit_name": "Stage 1 Filtration",
            "purification_type": "multi_stage",
            "flow_rate_lpm": 150.0,
            "efficiency_percent": 98.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert purification_response.status_code == 200

    # 3. Create irrigation system
    irrigation_response = client.post(
        "/api/v1/water/irrigation",
        json={
            "system_name": "Main Garden Irrigation",
            "irrigation_type": "sprinkler",
            "scheduled_frequency_minutes": 180,
            "water_per_cycle_liters": 200.0,
            "soil_moisture_target_percent": 70.0,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert irrigation_response.status_code == 200

    # 4. Record initial water quality
    quality_response = client.post(
        "/api/v1/water/quality",
        json={
            "reading_location": "collection",
            "ph_level": 6.8,
            "turbidity_ntu": 2.0,
            "temperature_celsius": 20.0,
            "contamination_detected": False,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert quality_response.status_code == 200
    assert quality_response.json()["overall_quality_status"] == "good"

    # 5. Create recycling loop
    recycling_response = client.post(
        "/api/v1/water/recycling",
        json={
            "loop_name": "Condensate Recovery",
            "loop_type": "condensate_recovery",
            "source_system": "HVAC System",
            "destination_system": "Collection Tank",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert recycling_response.status_code == 200

    # 6. Verify all systems are retrievable
    all_collections = client.get(
        "/api/v1/water/collection",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(all_collections.json()) == 1

    all_purifications = client.get(
        "/api/v1/water/purification",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(all_purifications.json()) == 1

    all_irrigations = client.get(
        "/api/v1/water/irrigation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(all_irrigations.json()) == 1

    all_recyclings = client.get(
        "/api/v1/water/recycling",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert len(all_recyclings.json()) == 1


def test_tenant_isolation_water_systems(test_db):
    """Test that water systems are isolated by tenant."""
    # Setup: Create two tenants
    tenant1 = create_tenant(test_db, "isolation_test_tenant_001")
    tenant2 = create_tenant(test_db, "isolation_test_tenant_002")
    user1 = create_operator_user(test_db, "operator1@test.com", tenant1.id)
    user2 = create_operator_user(test_db, "operator2@test.com", tenant2.id)
    token1 = get_token_for_user(user1)
    token2 = get_token_for_user(user2)

    # Create collection system for tenant 1
    client.post(
        "/api/v1/water/collection",
        json={
            "system_name": "Tenant 1 Collection",
            "collection_type": "rainfall",
            "capacity_liters": 5000.0,
        },
        headers={"Authorization": f"Bearer {token1}"},
    )

    # Create collection system for tenant 2
    client.post(
        "/api/v1/water/collection",
        json={
            "system_name": "Tenant 2 Collection",
            "collection_type": "greywater",
            "capacity_liters": 3000.0,
        },
        headers={"Authorization": f"Bearer {token2}"},
    )

    # Verify tenant 1 only sees their system
    response1 = client.get(
        "/api/v1/water/collection",
        headers={"Authorization": f"Bearer {token1}"},
    )
    systems1 = response1.json()
    assert len(systems1) == 1
    assert systems1[0]["system_name"] == "Tenant 1 Collection"

    # Verify tenant 2 only sees their system
    response2 = client.get(
        "/api/v1/water/collection",
        headers={"Authorization": f"Bearer {token2}"},
    )
    systems2 = response2.json()
    assert len(systems2) == 1
    assert systems2[0]["system_name"] == "Tenant 2 Collection"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
