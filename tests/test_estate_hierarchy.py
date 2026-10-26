from backend.models.estate_hierarchy import Estate, EstateNode
from backend.models_scene import SceneEntity


def test_estate_hierarchy_parent_chain(db):
    estate = Estate(tenant_id=1, name="Innovation Estate")
    db.add(estate)
    db.commit()
    db.refresh(estate)

    zone = EstateNode(estate_id=estate.id, node_type="zone", name="Agricultural Biosphere")
    db.add(zone)
    db.commit()
    db.refresh(zone)

    building = EstateNode(
        estate_id=estate.id,
        parent_id=zone.id,
        node_type="building",
        name="R&D Laboratory",
    )
    db.add(building)
    db.commit()

    assert building.parent_id == zone.id
    assert db.query(EstateNode).filter_by(estate_id=estate.id).count() == 2


def test_estate_layout_mutations_are_audited(client):
    headers = {"Authorization": "Bearer test-token"}
    created = client.post(
        "/api/v1/estate-layout",
        headers=headers,
        json={"name": "Audited Estate", "layout": {"width_m": 30, "depth_m": 20}},
    )
    assert created.status_code == 200, created.text
    estate_id = created.json()["id"]

    node = client.post(
        f"/api/v1/estate-layout/{estate_id}/nodes",
        headers=headers,
        json={
            "node_type": "zone",
            "name": "North greenhouse",
            "position": {"x": 2, "y": 0, "z": 3},
            "dimensions": {"x": 12, "y": 4, "z": 8},
        },
    )
    assert node.status_code == 200, node.text

    response = client.get("/api/v1/audit?limit=100", headers=headers)
    assert response.status_code == 200, response.text
    events = response.json()
    assert any(
        event["event_type"] == "estate_created"
        and event["entity_type"] == "estate"
        and event["entity_id"] == str(estate_id)
        for event in events
    )
    assert any(
        event["event_type"] == "estate_node_created"
        and event["entity_type"] == "estate_node"
        and event["entity_id"] == str(node.json()["id"])
        for event in events
    )


def test_scene_entity_lifecycle_is_tenant_scoped_and_audited(client, test_db):
    with test_db() as db:
        db.add(SceneEntity(name="Other tenant object", tenant_id=2, type="sensor"))
        db.commit()

    headers = {"Authorization": "Bearer test-token"}
    listed = client.get("/api/v1/scene/entities", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json() == []

    payload = {
        "name": "Greenhouse pump",
        "type": "pump",
        "model": "pump-v1",
        "x": 2.5,
        "y": 0,
        "z": 3.5,
        "rotation": 90,
        "state": {"status": "idle"},
    }
    created = client.post("/api/v1/scene/entities", headers=headers, json=payload)
    assert created.status_code == 200, created.text
    entity_id = created.json()["id"]

    payload["state"] = {"status": "running"}
    updated = client.put(
        f"/api/v1/scene/entities/{entity_id}", headers=headers, json=payload
    )
    assert updated.status_code == 200, updated.text

    deleted = client.delete(f"/api/v1/scene/entities/{entity_id}", headers=headers)
    assert deleted.status_code == 200, deleted.text

    response = client.get("/api/v1/audit?limit=100", headers=headers)
    assert response.status_code == 200, response.text
    events = [
        event for event in response.json()
        if event["entity_type"] == "scene_entity" and event["entity_id"] == str(entity_id)
    ]
    assert {event["event_type"] for event in events} == {
        "scene_entity_created", "scene_entity_updated", "scene_entity_deleted"
    }


def test_legacy_scene_admin_job_is_tenant_scoped_and_audited(client):
    headers = {"Authorization": "Bearer test-token"}
    created = client.post(
        "/api/v1/scene/admin/job",
        headers=headers,
        json={
            "name": "Tenant-bound inspection",
            "command": "inspect",
            "parameters": {"mode": "visual"},
            "tenant_id": 999,
        },
    )
    assert created.status_code == 200, created.text
    job_id = created.json()["id"]

    jobs = client.get("/api/v1/scene/admin/jobs", headers=headers)
    assert jobs.status_code == 200, jobs.text
    assert [job["id"] for job in jobs.json()] == [job_id]

    audit = client.get("/api/v1/audit?limit=100", headers=headers)
    assert audit.status_code == 200, audit.text
    assert any(
        event["event_type"] == "scene_automation_job_created"
        and event["entity_type"] == "automation_job"
        and event["entity_id"] == str(job_id)
        for event in audit.json()
    )

    global_control = client.post("/api/v1/scene/admin/pause", headers=headers)
    assert global_control.status_code == 403
