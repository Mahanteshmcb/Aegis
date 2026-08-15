"""Simple automation service for Phase 2 Day 72.

Listens to generated sensor readings (via direct calls from realtime emitter)
and triggers basic automation: when a soil moisture reading is below threshold,
create a system alert and (simulated) irrigation command.
"""
import asyncio
import logging
from datetime import datetime

from backend.database import SessionLocal
from backend import crud

logger = logging.getLogger(__name__)

# Thresholds (could be loaded from tenant settings later)
SOIL_MOISTURE_THRESHOLD = 30.0  # percent


async def process_sensor_reading(reading: dict):
    """Process a single sensor reading and run automation rules."""
    try:
        sensor_id = reading.get("sensor_id")
        system = reading.get("system")
        value = reading.get("value")

        # Only handle numeric values
        try:
            value_num = float(value)
        except Exception:
            return

        # Determine sensor info and tenant
        db = SessionLocal()
        tenant_id = None
        sensor_type = (reading.get("type") or "").lower()
        try:
            # If sensor_id is numeric, try to resolve Sensor record
            sensor_obj = None
            try:
                sid_int = int(sensor_id)
            except Exception:
                sid_int = None

            if sid_int is not None:
                sensor_obj = crud.get_sensor(db, sid_int)
            else:
                # Try to match by name when a string sensor_id was emitted
                if isinstance(sensor_id, str):
                    sensor_obj = db.query(__import__('backend').models_db.Sensor).filter_by(name=sensor_id).first()

            if sensor_obj:
                tenant_id = sensor_obj.tenant_id
                sensor_type = (sensor_obj.type or sensor_type or "").lower()
        except Exception:
            logger.exception("Error resolving sensor info")

        # Fallback tenant
        if tenant_id is None:
            tenant_id = 1

        # Load tenant-specific threshold if provided in tenant.settings
        threshold = SOIL_MOISTURE_THRESHOLD
        try:
            tenant = crud.get_tenant(db, tenant_id)
            if tenant and getattr(tenant, 'settings', None):
                t_settings = tenant.settings or {}
                threshold = t_settings.get('automation', {}).get('soil_moisture_threshold', threshold)
        except Exception:
            logger.debug("Could not load tenant settings, using default threshold")

        # Soil moisture automation
        if "soil" in sensor_type or system == "water":
            if value_num < float(threshold):
                try:
                    alert = crud.create_system_alert(db, crud.schemas.SystemAlertCreate(
                        tenant_id=tenant_id,
                        alert_type="irrigation_needed",
                        severity="medium",
                        title="Soil moisture low",
                        message=f"Sensor {sensor_id} reported low soil moisture ({value_num})",
                        source="automation",
                        data={"sensor_id": sensor_id, "value": value_num},
                    ))
                    logger.info("Automation created alert id=%s for sensor=%s", getattr(alert, 'id', None), sensor_id)
                except Exception:
                    logger.exception("Failed to create automation alert")

                # Simulate irrigation command dispatch (async sleep to mimic remote call)
                await asyncio.sleep(0.1)
                logger.info("Simulated dispatch: irrigation started for sensor %s", sensor_id)
        db.close()

    except Exception:
        logger.exception("Error processing sensor reading in automation")
