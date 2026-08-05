"""
Sensor health monitor: background task that checks sensor liveness and creates safety events.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from backend.database import SessionLocal
from backend.models.safety import SafetyEvent
from backend.services import broadcast

logger = logging.getLogger(__name__)


async def _sensor_monitor_loop(stop_event: asyncio.Event, stale_seconds: int = 300):
    logger.info("Sensor health monitor started")
    try:
        while not stop_event.is_set():
            session = SessionLocal()
            try:
                cutoff = datetime.utcnow() - timedelta(seconds=stale_seconds)
                from backend import models_db as mdb
                sensors = session.query(mdb.Sensor).all()
                for s in sensors:
                    last = s.last_reading or {}
                    ts = None
                    try:
                        ts_str = last.get('timestamp')
                        if ts_str:
                            ts = datetime.fromisoformat(ts_str)
                    except Exception:
                        ts = None
                    if not ts or ts < cutoff:
                        # create a safety event if sensor stale
                        evt = SafetyEvent(tenant_id=s.tenant_id, message=f"Sensor {s.id} stale or offline", severity="warning")
                        session.add(evt)
                        # publish to SSE clients
                        try:
                            await broadcast.publish({
                                "type": "safety_event",
                                "tenant_id": s.tenant_id,
                                "message": evt.message,
                                "severity": evt.severity,
                                "source": "sensor_monitor",
                            })
                        except Exception:
                            logger.exception("Failed to publish sensor stale event")
                session.commit()
            except Exception as e:
                logger.exception("Sensor monitor error: %s", e)
                session.rollback()
            finally:
                try:
                    session.close()
                except Exception:
                    pass

            await asyncio.wait([stop_event.wait()], timeout=60)
    except asyncio.CancelledError:
        logger.info("Sensor health monitor cancelled")


class SensorMonitor:
    def __init__(self):
        self._task = None
        self._stop_event = asyncio.Event()

    def start(self):
        if self._task is None:
            self._stop_event = asyncio.Event()
            self._task = asyncio.create_task(_sensor_monitor_loop(self._stop_event))
        return self._task

    async def stop(self):
        if self._task:
            self._stop_event.set()
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None


_global_monitor = SensorMonitor()


def get_sensor_monitor():
    return _global_monitor
