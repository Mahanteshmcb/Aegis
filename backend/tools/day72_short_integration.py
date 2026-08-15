import asyncio
import logging
import time
import ssl
import os

# SSL workaround
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except Exception:
    pass
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
try:
    ssl.SSLContext._load_windows_store_certs = lambda self, storename, purpose: None
except Exception:
    pass

from backend import database
from backend.database import SessionLocal
from backend import realtime
from backend import crud
from backend import models as _models  # ensure models package is importable
import backend.models.environmental

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("day72_short")


def seed(db):
    tenant_id = 1
    sensors = [
        {"name": "Test Soil Probe 1", "type": "soil_moisture", "location": "Test Field", "zone_id": None},
        {"name": "Test Soil Probe 2", "type": "soil_moisture", "location": "Test Field", "zone_id": None},
    ]
    try:
        crud.bulk_import_sensors(db, tenant_id, sensors)
        logger.info("Seeded sensors")
    except Exception as exc:
        logger.warning("Sensor seeding failed: %s", exc)

    task = {
        "task_id": f"day72-task-{int(time.time())}",
        "operation_type": "inspect_zone",
        "requested_robot_id": "sim-robot-short",
        "zone_id": None,
        "priority": 5,
        "task_detail": {"action": "inspect"},
        "metadata": {},
        "timeout_seconds": 60,
        "status": "pending",
    }
    from backend import schemas as _schemas
    try:
        crud.create_scheduled_task(db, _schemas.ScheduledTaskCreate(**task), tenant_id)
        logger.info("Seeded scheduled robot task")
    except Exception as exc:
        logger.warning("Scheduled task seeding failed: %s", exc)


async def run_short():
    # Ensure all ORM model modules are imported before creating metadata
    try:
        import backend.models.environmental
    except Exception:
        pass
    database.init_db()
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()

    loop = asyncio.get_event_loop()
    realtime.start_background_emitters(loop)
    logger.info("Emitters started for short integration run")
    # Let emitters run for a short period to generate readings and robot transitions
    await asyncio.sleep(6)
    await realtime.stop_background_emitters()

    # Inspect DB outcomes using sqlite3 to avoid ORM mapper issues in this short run
    import sqlite3
    from backend.config import settings

    db_path = settings.database_url.replace("sqlite:///", "")
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    print("Recent system_alerts:")
    for r in cur.execute('SELECT id, tenant_id, data, created_at FROM system_alerts ORDER BY id DESC LIMIT 10'):
        print(r)
    print("\nRecent scheduled_robotic_tasks:")
    for r in cur.execute('SELECT id, task_id, status, assigned_robot_id, updated_at FROM scheduled_robotic_tasks ORDER BY id DESC LIMIT 10'):
        print(r)
    con.close()


if __name__ == '__main__':
    try:
        asyncio.run(run_short())
    except KeyboardInterrupt:
        logger.info("Interrupted")
