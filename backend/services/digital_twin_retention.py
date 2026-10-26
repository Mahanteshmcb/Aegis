"""Scheduled retention cleanup for digital-twin telemetry and camera media."""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
import uuid

from backend.config import settings
from backend.database import SessionLocal
from backend.models_db import DigitalTwinMedia, DigitalTwinTelemetry

logger = logging.getLogger(__name__)


def cleanup_expired_digital_twin_data(now: datetime | None = None) -> dict[str, int]:
    current_time = now or datetime.utcnow()
    telemetry_cutoff = current_time - timedelta(days=settings.digital_twin_telemetry_retention_days)
    removed_telemetry = 0
    removed_media = 0
    with SessionLocal() as db:
        removed_telemetry = db.query(DigitalTwinTelemetry).filter(
            DigitalTwinTelemetry.recorded_at < telemetry_cutoff
        ).delete(synchronize_session=False)

        expired = db.query(DigitalTwinMedia).filter(
            DigitalTwinMedia.expires_at <= current_time
        ).all()
        root = Path(settings.digital_twin_media_dir).resolve()
        for media in expired:
            try:
                storage_key = str(uuid.UUID(media.storage_key))
            except ValueError:
                logger.error("Skipping media cleanup for invalid storage key on record %s", media.id)
                continue
            path = root / storage_key
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                logger.exception("Unable to remove expired digital-twin media record %s", media.id)
                continue
            db.delete(media)
            removed_media += 1
        db.commit()
    return {"telemetry": removed_telemetry, "media": removed_media}


async def retention_cleanup_loop():
    while True:
        try:
            result = await asyncio.to_thread(cleanup_expired_digital_twin_data)
            logger.info("Digital-twin retention cleanup removed %s telemetry records and %s media files", result["telemetry"], result["media"])
        except Exception:
            logger.exception("Digital-twin retention cleanup failed")
        await asyncio.sleep(24 * 60 * 60)
