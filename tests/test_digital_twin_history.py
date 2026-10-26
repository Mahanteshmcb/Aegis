from datetime import datetime, timedelta
import random

from backend.config import settings
from backend.models.digital_twin import DigitalTwinDevice
from backend.models_db import DigitalTwinMedia, DigitalTwinTelemetry
from backend.services.digital_twin import tick_once


def test_simulation_tick_persists_device_snapshot(test_db):
    db = test_db()
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="persisted-tick-sensor",
        name="Persisted tick sensor",
        kind="sensor",
        device_type="temperature",
        state={"value": 24.5},
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    snapshots = tick_once(db, tenant_id=1, rng=random.Random(7))

    persisted = db.query(DigitalTwinTelemetry).filter_by(
        tenant_id=1,
        device_id=device.id,
    ).one()
    assert persisted.snapshot["device_id"] == snapshots[0]["device_id"]
    assert persisted.snapshot["state"] == snapshots[0]["state"]
    db.close()


def test_persisted_device_history_is_tenant_scoped(client, test_db):
    db = test_db()
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="history-sensor",
        name="History sensor",
        kind="sensor",
        device_type="temperature",
        state={"value": 24.5, "unit": "C"},
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    db.add(DigitalTwinTelemetry(
        tenant_id=1,
        device_id=device.id,
        snapshot={"device_id": device.device_id, "state": device.state},
        recorded_at=datetime.utcnow(),
    ))
    db.commit()

    response = client.get(
        f"/api/v1/digital-twin/devices/{device.id}/history?limit=10",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200
    assert response.json()["data"][0]["snapshot"]["state"]["value"] == 24.5
    db.close()


def test_camera_media_upload_download_and_delete(client, test_db, monkeypatch, tmp_path):
    media_dir = tmp_path / "camera-media"
    monkeypatch.setattr(settings, "digital_twin_media_dir", str(media_dir))
    db = test_db()
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="camera-1",
        name="East camera",
        kind="sensor",
        device_type="camera",
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    uploaded = client.post(
        f"/api/v1/digital-twin/devices/{device.id}/media",
        headers={"Authorization": "Bearer test-token"},
        files={"file": ("clip.mp4", b"test-video-data", "video/mp4")},
    )
    assert uploaded.status_code == 201
    media = uploaded.json()
    assert media["name"] == "clip.mp4"
    assert media["expires_at"]

    listed = client.get(
        f"/api/v1/digital-twin/devices/{device.id}/media",
        headers={"Authorization": "Bearer test-token"},
    )
    assert listed.status_code == 200
    assert listed.json()["data"][0]["id"] == media["id"]

    downloaded = client.get(
        media["content_url"],
        headers={"Authorization": "Bearer test-token"},
    )
    assert downloaded.status_code == 200
    assert downloaded.content == b"test-video-data"

    deleted = client.delete(
        f"/api/v1/digital-twin/media/{media['id']}",
        headers={"Authorization": "Bearer test-token"},
    )
    assert deleted.status_code == 204
    assert not any(media_dir.iterdir())
    db.close()


def test_media_retention_removes_expired_records_and_files(client, test_db, monkeypatch, tmp_path):
    media_dir = tmp_path / "retained-media"
    media_dir.mkdir()
    monkeypatch.setattr(settings, "digital_twin_media_dir", str(media_dir))
    db = test_db()
    device = DigitalTwinDevice(
        tenant_id=1,
        device_id="retention-camera",
        name="Retention camera",
        kind="sensor",
        device_type="camera",
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    media_key = "cb459e9a-0b56-4b5a-a224-91d011c7d403"
    (media_dir / media_key).write_bytes(b"expired")
    db.add(DigitalTwinMedia(
        tenant_id=1,
        device_id=device.id,
        storage_key=media_key,
        original_name="old.mp4",
        content_type="video/mp4",
        size_bytes=7,
        created_at=datetime.utcnow() - timedelta(days=40),
        expires_at=datetime.utcnow() - timedelta(days=1),
    ))
    db.commit()

    from backend.services.digital_twin_retention import cleanup_expired_digital_twin_data
    monkeypatch.setattr("backend.services.digital_twin_retention.SessionLocal", test_db)
    result = cleanup_expired_digital_twin_data()

    assert result["media"] == 1
    assert not (media_dir / media_key).exists()
    assert db.query(DigitalTwinMedia).count() == 0
    db.close()
