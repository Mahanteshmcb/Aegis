"""
Comprehensive test suite for Day 67 Waste Management system.
Tests all waste operations: containers, sorting, composting, recycling, hazardous waste, and metrics.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.database import Base, engine
from backend.dependencies import get_db
from tests.conftest import create_tenant, create_operator_user, get_token_for_user


client = TestClient(app)


class TestWasteManagement:
    @pytest.fixture(autouse=True)
    def setup(self, test_db):
        """Create test data before each test."""
        self.db = test_db
        self.tenant = create_tenant(self.db, "waste_test_estate")
        self.user = create_operator_user(
            self.db,
            "operator@waste.test",
            self.tenant.id
        )
        self.token = get_token_for_user(self.user)
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_waste_container_creation_and_retrieval(self):
        """Test creating waste containers and retrieving them."""
        # Create multiple containers
        container_payload = {
            "container_name": "Organic Waste Bin A1",
            "waste_type": "organic",
            "capacity_kg": 200.0,
            "location": "Zone 1",
            "emptying_frequency_days": 7,
        }
        response = client.post(
            "/api/v1/waste/containers",
            json=container_payload,
            headers=self.headers,
        )
        assert response.status_code == 200
        container = response.json()
        assert container["container_name"] == "Organic Waste Bin A1"
        assert container["waste_type"] == "organic"
        assert container["capacity_kg"] == 200.0
        assert container["current_load_kg"] == 0.0
        assert container["active"] is True

        # Retrieve all containers
        response = client.get(
            "/api/v1/waste/containers",
            headers=self.headers,
        )
        assert response.status_code == 200
        containers = response.json()
        assert len(containers) >= 1
        assert any(c["container_name"] == "Organic Waste Bin A1" for c in containers)

    def test_waste_sorting_with_contamination_detection(self):
        """Test waste sorting with automatic contamination detection and quality scoring."""
        # Record clean sorting
        clean_sort = {
            "waste_type": "recyclable",
            "weight_kg": 50.0,
            "source_location": "Zone 2",
            "destination_container": "Recycling Bin",
            "sorting_method": "automated",
            "contamination_detected": False,
        }
        response = client.post(
            "/api/v1/waste/sorting",
            json=clean_sort,
            headers=self.headers,
        )
        assert response.status_code == 200
        log = response.json()
        assert log["weight_kg"] == 50.0
        assert log["contamination_detected"] is False
        assert log["quality_score"] == 100.0  # Perfect quality for non-contaminated

        # Record contaminated sorting
        contaminated_sort = {
            "waste_type": "organic",
            "weight_kg": 30.0,
            "source_location": "Zone 1",
            "destination_container": "Organic Bin",
            "sorting_method": "manual",
            "contamination_detected": True,
            "contamination_type": "plastic_mixed_in",
        }
        response = client.post(
            "/api/v1/waste/sorting",
            json=contaminated_sort,
            headers=self.headers,
        )
        assert response.status_code == 200
        log = response.json()
        assert log["contamination_detected"] is True
        assert log["contamination_type"] == "plastic_mixed_in"
        assert log["quality_score"] < 100.0  # Reduced for contamination

        # Verify retrieval
        response = client.get(
            "/api/v1/waste/sorting",
            headers=self.headers,
        )
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) >= 2

    def test_composting_process_lifecycle(self):
        """Test composting process lifecycle: preparing -> active -> curing -> completed."""
        composting_payload = {
            "process_name": "Main Compost Pile",
            "pile_id": "CP-001",
            "organic_input_kg": 1000.0,
            "moisture_percent": 55.0,
            "temperature_celsius": 45.0,
            "carbon_nitrogen_ratio": 25.0,
        }

        # Create composting process
        response = client.post(
            "/api/v1/waste/composting",
            json=composting_payload,
            headers=self.headers,
        )
        assert response.status_code == 200
        process = response.json()
        assert process["process_name"] == "Main Compost Pile"
        assert process["pile_id"] == "CP-001"
        assert process["status"] == "preparing"  # Initial status
        assert process["organic_input_kg"] == 1000.0
        assert process["current_weight_kg"] == 1000.0
        assert process["temperature_celsius"] == 45.0

        # Retrieve composting processes
        response = client.get(
            "/api/v1/waste/composting",
            headers=self.headers,
        )
        assert response.status_code == 200
        processes = response.json()
        assert len(processes) >= 1
        assert any(p["pile_id"] == "CP-001" for p in processes)

    def test_recycling_process_efficiency_tracking(self):
        """Test recycling process with recovery rate and environmental impact scoring."""
        recycling_payload = {
            "process_name": "Plastic Recycling Batch 1",
            "material_type": "plastic",
            "input_weight_kg": 500.0,
            "processing_method": "mechanical",
            "destination_facility": "Regional Recycling Center",
        }

        response = client.post(
            "/api/v1/waste/recycling",
            json=recycling_payload,
            headers=self.headers,
        )
        assert response.status_code == 200
        process = response.json()
        assert process["process_name"] == "Plastic Recycling Batch 1"
        assert process["material_type"] == "plastic"
        assert process["input_weight_kg"] == 500.0
        assert process["status"] == "pending"
        assert process["recovery_rate_percent"] >= 0.0
        assert process["output_weight_kg"] >= 0.0
        assert "environmental_impact_score" in process

        # Retrieve all recycling processes
        response = client.get(
            "/api/v1/waste/recycling",
            headers=self.headers,
        )
        assert response.status_code == 200
        processes = response.json()
        assert len(processes) >= 1

    def test_hazardous_waste_containment_and_safety(self):
        """Test hazardous waste storage with chemical classification and safety requirements."""
        hazardous_payload = {
            "container_id": "HAZ-001",
            "chemical_name": "Pesticide Type A",
            "chemical_type": "pesticide",
            "cas_number": "1234-56-7",
            "quantity_liters": 50.0,
            "concentration_percent": 95.0,
            "hazard_classification": "GHS-Acute Toxicity",
            "physical_state": "liquid",
            "storage_location": "Hazmat Storage Zone",
            "storage_temperature_min": 5.0,
            "storage_temperature_max": 25.0,
            "ventilation_required": True,
        }

        response = client.post(
            "/api/v1/waste/hazardous",
            json=hazardous_payload,
            headers=self.headers,
        )
        assert response.status_code == 200
        storage = response.json()
        assert storage["chemical_name"] == "Pesticide Type A"
        assert storage["chemical_type"] == "pesticide"
        assert storage["cas_number"] == "1234-56-7"
        assert storage["quantity_liters"] == 50.0
        assert storage["is_sealed"] is True  # Default sealed
        assert storage["container_condition"] == "good"

        # Retrieve all hazardous waste
        response = client.get(
            "/api/v1/waste/hazardous",
            headers=self.headers,
        )
        assert response.status_code == 200
        hazardous_list = response.json()
        assert len(hazardous_list) >= 1
        assert any(h["chemical_name"] == "Pesticide Type A" for h in hazardous_list)

    def test_complete_waste_workflow(self):
        """Integration test: complete workflow with all waste system types."""
        # 1. Create container
        container_response = client.post(
            "/api/v1/waste/containers",
            json={
                "container_name": "Multi-type Bin",
                "waste_type": "inert",
                "capacity_kg": 300.0,
                "location": "Central Collection Point",
            },
            headers=self.headers,
        )
        assert container_response.status_code == 200
        container = container_response.json()

        # 2. Record sorting
        sort_response = client.post(
            "/api/v1/waste/sorting",
            json={
                "waste_type": "inert",
                "weight_kg": 75.0,
                "source_location": "Construction Site",
                "sorting_method": "manual",
            },
            headers=self.headers,
        )
        assert sort_response.status_code == 200

        # 3. Start composting
        compost_response = client.post(
            "/api/v1/waste/composting",
            json={
                "process_name": "Integration Test Compost",
                "pile_id": "INT-CP-001",
                "organic_input_kg": 500.0,
                "moisture_percent": 50.0,
                "temperature_celsius": 50.0,
            },
            headers=self.headers,
        )
        assert compost_response.status_code == 200

        # 4. Start recycling
        recycle_response = client.post(
            "/api/v1/waste/recycling",
            json={
                "process_name": "Integration Test Recycle",
                "material_type": "glass",
                "input_weight_kg": 100.0,
            },
            headers=self.headers,
        )
        assert recycle_response.status_code == 200

        # 5. Register hazardous waste
        hazard_response = client.post(
            "/api/v1/waste/hazardous",
            json={
                "container_id": "INT-HAZ-001",
                "chemical_name": "Test Chemical",
                "chemical_type": "solvent",
                "quantity_liters": 25.0,
                "physical_state": "liquid",
                "storage_location": "Safe Storage",
            },
            headers=self.headers,
        )
        assert hazard_response.status_code == 200

        # 6. Retrieve metrics
        metrics_response = client.get(
            "/api/v1/waste/metrics",
            headers=self.headers,
        )
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert "total_waste_collected_kg" in metrics
        assert "recycling_rate_percent" in metrics
        assert "waste_diversion_rate_percent" in metrics

    def test_tenant_isolation_waste_systems(self):
        """Verify that each tenant sees only their own waste systems."""
        # Tenant 1 creates container
        tenant1_container = {
            "container_name": "Tenant1 Container",
            "waste_type": "organic",
            "capacity_kg": 100.0,
        }
        response1 = client.post(
            "/api/v1/waste/containers",
            json=tenant1_container,
            headers=self.headers,
        )
        assert response1.status_code == 200
        container1 = response1.json()

        # Create tenant 2 and get token
        tenant2 = create_tenant(self.db, "waste_test_estate_2")
        user2 = create_operator_user(self.db, "operator2@waste.test", tenant2.id)
        token2 = get_token_for_user(user2)
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Tenant 2 creates container
        tenant2_container = {
            "container_name": "Tenant2 Container",
            "waste_type": "recyclable",
            "capacity_kg": 150.0,
        }
        response2 = client.post(
            "/api/v1/waste/containers",
            json=tenant2_container,
            headers=headers2,
        )
        assert response2.status_code == 200

        # Tenant 1 retrieves containers - should only see their own
        list_response1 = client.get(
            "/api/v1/waste/containers",
            headers=self.headers,
        )
        assert list_response1.status_code == 200
        containers1 = list_response1.json()
        assert all(c["container_name"] != "Tenant2 Container" for c in containers1)
        assert any(c["container_name"] == "Tenant1 Container" for c in containers1)

        # Tenant 2 retrieves containers - should only see their own
        list_response2 = client.get(
            "/api/v1/waste/containers",
            headers=headers2,
        )
        assert list_response2.status_code == 200
        containers2 = list_response2.json()
        assert all(c["container_name"] != "Tenant1 Container" for c in containers2)
        assert any(c["container_name"] == "Tenant2 Container" for c in containers2)

    def test_waste_processing_log_with_efficiency_calculation(self):
        """Test waste processing operations with efficiency metrics and emissions tracking."""
        processing_payload = {
            "operation_type": "incineration",
            "waste_category": "hazardous",
            "input_weight_kg": 100.0,
            "output_weight_kg": 5.0,
            "energy_consumed_kwh": 50.0,
            "emissions_kg_co2": 25.0,
            "operator": "John Smith",
            "notes": "High temperature incineration of chemical waste",
        }

        response = client.post(
            "/api/v1/waste/processing",
            json=processing_payload,
            headers=self.headers,
        )
        assert response.status_code == 200
        log = response.json()
        assert log["operation_type"] == "incineration"
        assert log["input_weight_kg"] == 100.0
        assert log["output_weight_kg"] == 5.0
        # Efficiency: (5.0 / 100.0) * 100 = 5%
        assert log["processing_efficiency_percent"] == 5.0


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    Base.metadata.create_all(bind=engine)
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield db
    
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()
