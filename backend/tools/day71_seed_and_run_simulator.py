"""Day 71 helper: seed simulated devices and start realtime emitters.

Run from the workspace root with the `aegis` Python environment active.
Example:
    cd backend
    python tools/day71_seed_and_run_simulator.py
"""
import asyncio
import logging
import time
import ssl
import os

# Apply Windows SSL workaround (matches backend/main.py) to avoid aiohttp import errors
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
from backend import crud
from backend.database import SessionLocal
from backend import realtime
from backend import models_db as models

logger = logging.getLogger("day71")


def resolve_seed_tenant_id(db):
    tenant = db.query(models.Tenant).filter(models.Tenant.name == "Aegis Tenant").first()
    if tenant is not None:
        return tenant.id
    tenant = db.query(models.Tenant).filter(models.Tenant.name == "Default Tenant").first()
    if tenant is not None:
        return tenant.id
    return 1


def seed_simulated_sensors(db):
    tenant_id = resolve_seed_tenant_id(db)
    sensors = [
        {"name": "Sim Soil Probe 1", "type": "soil_moisture", "location": "Field A", "zone_id": None},
        {"name": "Sim Energy Inverter 1", "type": "inverter", "location": "Power Shed", "zone_id": None},
        {"name": "Sim Acoustic Pest Monitor 1", "type": "acoustic_pest", "location": "Canopy North", "zone_id": None},
    ]
    result = crud.bulk_import_sensors(db, tenant_id, sensors)
    logger.info("Bulk import sensors result: %s", result)


def seed_simulated_robot_task(db):
    tenant_id = resolve_seed_tenant_id(db)
    task = {
        "task_id": f"day71-task-{int(time.time())}",
        "operation_type": "inspect_zone",
        "requested_robot_id": "sim-robot-1",
        "zone_id": None,
        "priority": 5,
        "task_detail": {"action": "inspect", "notes": "Daily inspection (simulated)"},
        "metadata": {},
        "timeout_seconds": 120,
        "status": "pending",
    }
    try:
        db_task = crud.create_scheduled_task(db, crud.schemas.ScheduledTaskCreate(**task), tenant_id)
        logger.info("Created scheduled robot task: %s", db_task.task_id)
    except Exception as exc:
        logger.warning("Scheduled task creation failed: %s", exc)


async def start_emitters():
    loop = asyncio.get_event_loop()
    realtime.start_background_emitters(loop)
    logger.info("Realtime emitters started (background tasks)")
    # Keep running until cancelled
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        await realtime.stop_background_emitters()


def main():
    logging.basicConfig(level=logging.INFO)
    # Ensure DB and tables exist + sample seed
    # Import modules that register additional ORM models required by relationships
    try:
        import backend.models.environmental
    except Exception:
        pass
    database.init_db()

    db = SessionLocal()
    try:
        seed_simulated_sensors(db)
        # scheduled task creation relies on schemas; import here to avoid circular
        # import
        from backend import schemas as _schemas

        # crud.create_scheduled_task expects a ScheduledTaskCreate Pydantic model
        # Build minimal ScheduledTaskCreate equivalent
        task_create = _schemas.ScheduledTaskCreate(
            task_id=f"day71-task-{int(time.time())}",
            operation_type="inspect_zone",
            requested_robot_id="sim-robot-1",
            zone_id=None,
            priority=5,
            task_detail={"action": "inspect"},
            metadata={},
            timeout_seconds=120,
            status="pending",
        )
        try:
            crud.create_scheduled_task(db, task_create, tenant_id=resolve_seed_tenant_id(db))
            logger.info("Seeded scheduled robotic task")
        except Exception as exc:
            logger.warning("Could not seed scheduled task: %s", exc)
    finally:
        db.close()

    # Start realtime emitters to simulate telemetry
    try:
        asyncio.run(start_emitters())
    except KeyboardInterrupt:
        logger.info("Day71 simulator stopped by user")


if __name__ == "__main__":
    main()
