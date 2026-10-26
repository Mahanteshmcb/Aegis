from backend.services.estate_seed import build_estate_seed_snapshot
from backend.estate_config import DeviceConfig, EstateConfig, ZoneConfig, persist_estate_config
from backend.models.digital_twin import DigitalTwinDevice


def test_build_estate_seed_snapshot_has_realistic_systems():
    snapshot = build_estate_seed_snapshot()

    assert snapshot["site_name"] == "Aegis Estate"

    zone_names = {zone["name"] for zone in snapshot["zones"]}
    assert len(snapshot["zones"]) >= 8
    assert zone_names >= {
        "Main Greenhouse",
        "Hydroponic Plantation",
        "Multi-Level Agriculture",
        "Garden",
        "Swimming Pool",
        "Water Vault",
        "Waste Processing",
        "Robotics Bay",
        "Security Perimeter",
        "Office",
        "Server Room",
        "Warehouse",
    }

    device_ids = {device["device_id"] for device in snapshot["devices"]}
    assert {
        "greenhouse-temp-1",
        "hydroponic-ph-1",
        "pool-temp-1",
        "irrigation-pump-1",
        "field-rover-1",
        "waste-sorter-1",
        "perimeter-camera-1",
        "server-room-temp-1",
        "estate-solar-generation-1",
        "estate-battery-soc-1",
        "estate-load-meter-1",
    } <= device_ids

    water_devices = [device for device in snapshot["devices"] if device["zone_name"] == "Water Vault"]
    waste_devices = [device for device in snapshot["devices"] if device["zone_name"] == "Waste Processing"]
    automation_devices = [device for device in snapshot["devices"] if device["kind"] == "actuator"]

    assert water_devices
    assert waste_devices
    assert automation_devices


def test_estate_config_persists_object_shaped_twin_state(test_db):
    db = test_db()
    config = EstateConfig(
        estate_id="typed-estate",
        estate_type="farm",
        name="Typed estate",
        zones=[ZoneConfig(zone_id="north", name="North block", zone_type="field")],
        devices=[DeviceConfig(
            device_id="north-soil-probe",
            zone_id="north",
            type="SENSOR_SOIL_MOISTURE",
            position={"x": 12.0, "y": 0.0, "z": -4.0},
            metadata={"unit": "%"},
        )],
    )

    summary = persist_estate_config(config, db, tenant_id=1)
    twin = db.query(DigitalTwinDevice).filter_by(device_id="north-soil-probe").one()

    assert summary["devices"][0]["db_twin_id"] == twin.id
    assert twin.position == {"x": 12.0, "y": 0.0, "z": -4.0}
    assert isinstance(twin.state, dict)
    assert twin.state["unit"] == "%"
    assert twin.zone_id is not None
    db.close()
