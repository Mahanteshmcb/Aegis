from types import SimpleNamespace

from jose import jwt
import pytest
from fastapi import HTTPException

from backend.config import settings
from backend.database import Zone
from backend.dependencies import get_current_user, has_permission
from backend.models.digital_twin import DigitalTwinDevice
from backend.models_db import RoleDefinition, User
from backend.main import app
from backend.dependencies import get_current_user as current_user_dependency
from backend.routers.digital_twin import _validate_zone_ownership
from backend.routers.zones import ZoneResponse


def test_custom_role_permissions_are_resolved_for_the_role_tenant(test_db):
    db = test_db()
    role = RoleDefinition(
        tenant_id=1,
        key="zone_editor",
        name="Zone editor",
        permissions=["zones.manage"],
    )
    user = User(
        tenant_id=1,
        email="zone-editor@example.com",
        hashed_password="not-used",
        role="zone_editor",
    )
    db.add_all([role, user])
    db.commit()
    token = jwt.encode({"sub": str(user.id), "tenant_id": 1}, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    resolved = get_current_user(token=token, db=db)

    assert has_permission(resolved, "zones.manage")
    assert not has_permission(resolved, "devices.manage")
    db.close()


def test_custom_permissions_gate_zone_writes_and_persist_survey_geometry(client):
    original_override = app.dependency_overrides[current_user_dependency]
    try:
        app.dependency_overrides[current_user_dependency] = lambda: {
            "id": 5,
            "tenant_id": 1,
            "role": "zone_editor",
            "email": "zone-editor@example.com",
            "permissions": ["zones.manage"],
        }
        response = client.post(
            "/api/v1/zones",
            headers={"Authorization": "Bearer test-token"},
            json={
                "name": "Surveyed greenhouse",
                "spatial_position": {"x": 12.5, "y": 0, "z": -7},
                "dimensions": {"width": 18, "height": 4, "depth": 12},
                "spatial_status": "surveyed",
                "coordinate_system": "estate-local-y-up",
                "length_unit": "m",
                "orientation": {"x": 0, "y": 45, "z": 0},
            },
        )
        assert response.status_code == 200
        assert response.json()["spatial_status"] == "surveyed"
        assert response.json()["position"] == [12.5, 0, -7]
        assert response.json()["size"] == [18, 4, 12]
        assert response.json()["orientation"] == {"x": 0, "y": 45, "z": 0}
        original_updated_at = response.json()["updated_at"]

        updated = client.put(
            f"/api/v1/zones/{response.json()['id']}",
            headers={"Authorization": "******"},
            json={
                "expected_updated_at": original_updated_at,
                "orientation": {"x": 0, "y": 90, "z": 0},
            },
        )
        assert updated.status_code == 200
        assert updated.json()["orientation"] == {"x": 0, "y": 90, "z": 0}
        assert updated.json()["updated_at"] != original_updated_at
        stale = client.put(
            f"/api/v1/zones/{response.json()['id']}",
            headers={"Authorization": "******"},
            json={
                "expected_updated_at": original_updated_at,
                "orientation": {"x": 0, "y": 180, "z": 0},
            },
        )
        assert stale.status_code == 409

        app.dependency_overrides[current_user_dependency] = lambda: {
            "id": 6,
            "tenant_id": 1,
            "role": "custom_viewer",
            "email": "viewer@example.com",
            "permissions": [],
        }
        forbidden = client.post(
            "/api/v1/zones",
            headers={"Authorization": "Bearer test-token"},
            json={"name": "Forbidden zone"},
        )
        assert forbidden.status_code == 403
    finally:
        app.dependency_overrides[current_user_dependency] = original_override


def test_surveyed_zone_requires_complete_local_geometry(client):
    response = client.post(
        "/api/v1/zones",
        headers={"Authorization": "Bearer test-token"},
        json={
            "name": "Incomplete survey",
            "spatial_position": {"x": 0, "y": 0, "z": 0},
            "spatial_status": "surveyed",
            "coordinate_system": "estate-local-y-up",
        },
    )
    assert response.status_code == 422


def test_device_zone_assignment_is_tenant_scoped(test_db):
    db = test_db()
    zone = Zone(tenant_id=2, name="Other tenant zone")
    db.add(zone)
    db.commit()

    with pytest.raises(HTTPException) as error:
        _validate_zone_ownership(db, 1, zone.id)
    assert error.value.status_code == 404

    _validate_zone_ownership(db, 2, zone.id)
    db.close()


def test_deleting_zone_detaches_twin_assets(client, test_db):
    db = test_db()
    zone = Zone(tenant_id=1, name="Twin-owned zone")
    db.add(zone)
    db.commit()
    device = DigitalTwinDevice(
        tenant_id=1,
        zone_id=zone.id,
        device_id="zone-delete-rover",
        name="Zone rover",
        kind="robot",
        device_type="rover",
    )
    db.add(device)
    db.commit()
    zone_id = zone.id
    device_id = device.id
    db.close()

    original_override = app.dependency_overrides[current_user_dependency]
    try:
        app.dependency_overrides[current_user_dependency] = lambda: {
            "id": 7,
            "tenant_id": 1,
            "role": "admin",
            "email": "admin@example.com",
            "permissions": ["zones.manage"],
        }
        response = client.delete(f"/api/v1/zones/{zone_id}")
        assert response.status_code == 200

        verify_db = test_db()
        persisted = verify_db.query(DigitalTwinDevice).filter_by(id=device_id).one()
        assert persisted.zone_id is None
        verify_db.close()
    finally:
        app.dependency_overrides[current_user_dependency] = original_override


def test_zone_response_applies_geometry_defaults_to_legacy_nulls():
    legacy_zone = SimpleNamespace(
        id=1,
        name="Legacy zone",
        description="",
        location="Legacy zone",
        tenant_id=1,
        zone_id="1",
        spatial_position=None,
        dimensions=None,
        spatial_status=None,
        coordinate_system=None,
        length_unit=None,
    )

    response = ZoneResponse.model_validate(legacy_zone)

    assert response.spatial_status == "inferred"
    assert response.length_unit == "m"


def test_health_check_reports_database_connection(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"
