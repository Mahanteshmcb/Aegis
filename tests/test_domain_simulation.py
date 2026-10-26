from backend.models.storage import InventoryItem, StorageFacility
from backend.models.water import WaterCollectionSystem, WaterQualityReading
from backend.services.domain_simulation import seed_demo_resource_data
from tests.conftest import create_tenant


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def test_demo_resource_seed_is_idempotent_and_populates_empty_domains(test_db):
    db = test_db()
    tenant = create_tenant(db, "domain-simulation-seed")

    seed_demo_resource_data(db, tenant.id)
    seed_demo_resource_data(db, tenant.id)

    assert db.query(WaterCollectionSystem).filter_by(tenant_id=tenant.id).count() == 3
    assert db.query(StorageFacility).filter_by(tenant_id=tenant.id).count() == 2
    assert db.query(InventoryItem).filter_by(tenant_id=tenant.id).count() == 3
    db.close()


def test_canonical_estate_seed_also_initializes_resource_domains(test_db, monkeypatch):
    import backend.database as database

    db = test_db()
    tenant = create_tenant(db, "canonical-resource-seed")
    tenant_id = tenant.id
    monkeypatch.setattr(database, "engine", db.get_bind())
    monkeypatch.setattr(database, "SessionLocal", test_db)

    database._seed_canonical_estate_snapshot(tenant_id)

    assert db.query(WaterCollectionSystem).filter_by(tenant_id=tenant_id).count() == 3
    assert db.query(StorageFacility).filter_by(tenant_id=tenant_id).count() == 2
    assert db.query(InventoryItem).filter_by(tenant_id=tenant_id).count() == 3
    db.close()


def test_domain_simulation_advances_only_demo_state_and_preserves_measured_quality(client, test_db):
    db = test_db()
    tenant = create_tenant(db, "domain-simulation-advance")
    tenant_id = tenant.id
    seed_demo_resource_data(db, tenant_id)

    facility = db.query(StorageFacility).filter_by(tenant_id=tenant.id).first()
    actual_item = InventoryItem(
        tenant_id=tenant.id,
        facility_id=facility.id,
        name="User entered stock",
        quantity=17,
        unit="kg",
        lot_number="ACTUAL-LOT-1",
    )
    db.add(actual_item)
    db.commit()
    db.close()

    water = client.post("/api/v1/water/simulation/advance", json={"step_hours": 24}, headers=AUTH_HEADERS)
    waste = client.post("/api/v1/waste/simulation/advance", json={"step_hours": 24}, headers=AUTH_HEADERS)
    storage = client.post("/api/v1/storage/simulation/advance", json={"step_hours": 24}, headers=AUTH_HEADERS)

    assert water.status_code == 200
    assert water.json()["mode"] == "simulation"
    assert water.json()["rainfall_added_liters"] > 0
    assert "No synthetic water-quality readings" in water.json()["quality_readings_note"]
    assert waste.status_code == 200
    assert waste.json()["generated_waste_kg"] > 0
    assert waste.json()["recycled_output_kg"] > 0
    sorting_history = client.get("/api/v1/waste/sorting", headers=AUTH_HEADERS)
    processing_history = client.get("/api/v1/waste/processing", headers=AUTH_HEADERS)
    assert len(sorting_history.json()) == 3
    assert len(processing_history.json()) >= 2
    assert storage.status_code == 200
    assert storage.json()["inventory_items_advanced"] == 3
    assert storage.json()["consumed_by_unit"]["kg"] > 0

    db = test_db()
    assert db.query(WaterQualityReading).filter_by(tenant_id=tenant_id).count() == 0
    actual_item = db.query(InventoryItem).filter_by(lot_number="ACTUAL-LOT-1").one()
    assert actual_item.quantity == 17
    db.close()


def test_simulation_rejects_invalid_step_and_limits_to_tenant_demo_data(client):
    invalid = client.post(
        "/api/v1/water/simulation/advance",
        json={"step_hours": 0},
        headers=AUTH_HEADERS,
    )
    assert invalid.status_code == 422

    no_data = client.post(
        "/api/v1/storage/simulation/advance",
        json={"step_hours": 24},
        headers=AUTH_HEADERS,
    )
    assert no_data.status_code == 200
    assert no_data.json()["inventory_items_advanced"] == 0
