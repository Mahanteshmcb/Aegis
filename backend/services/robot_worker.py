import asyncio
import logging
import random
from datetime import datetime

from backend.database import SessionLocal
from backend import crud

logger = logging.getLogger(__name__)

async def robot_task_worker(poll_interval: float = 2.0):
    """Poll scheduled_robotic_tasks and simulate assignment/execution lifecycle.

    Transitions: pending -> assigned -> in_progress -> completed
    Emits socket events via `backend.realtime.sio` when transitions occur.
    """
    try:
        # Import sio lazily to avoid circular import at module import time
        from backend.realtime import sio
    except Exception:
        sio = None

    while True:
        try:
            with SessionLocal() as db:
                models_db = __import__('backend').models_db
                tasks = (
                    db.query(models_db.ScheduledRoboticTask)
                    .filter_by(status='pending')
                    .order_by(models_db.ScheduledRoboticTask.enqueue_time.asc())
                    .all()
                )
                for t in tasks:
                    # assign
                    assigned_robot = f"sim-robot-{random.randint(1,3)}"
                    try:
                        crud.update_scheduled_task_status(db, t, 'assigned', assigned_robot_id=assigned_robot)
                        logger.info("Assigned task %s to %s", t.task_id, assigned_robot)
                        if sio:
                            payload = {
                                'task_id': t.task_id,
                                'status': 'assigned',
                                'assigned_robot_id': assigned_robot,
                                'tenant_id': t.tenant_id,
                                'operation_type': t.operation_type,
                                'timestamp': datetime.utcnow().isoformat(),
                            }
                            asyncio.create_task(sio.emit('robot:task_update', payload))
                    except Exception:
                        logger.exception("Failed to assign task %s", t.task_id)

                    # short delay then mark in_progress
                    await asyncio.sleep(0.5 + random.random() * 0.5)
                    with SessionLocal() as db2:
                        try:
                            t2 = db2.query(__import__('backend').models_db.ScheduledRoboticTask).filter_by(id=t.id).first()
                            crud.update_scheduled_task_status(db2, t2, 'in_progress', assigned_robot_id=assigned_robot)
                            logger.info("Task %s in_progress", t.task_id)
                            if sio:
                                payload = {'task_id': t.task_id, 'status': 'in_progress', 'assigned_robot_id': assigned_robot, 'tenant_id': t.tenant_id, 'timestamp': datetime.utcnow().isoformat()}
                                asyncio.create_task(sio.emit('robot:task_update', payload))
                        except Exception:
                            logger.exception("Failed to set in_progress for %s", t.task_id)

                    # simulate work
                    await asyncio.sleep(1 + random.random() * 2)

                    with SessionLocal() as db3:
                        try:
                            t3 = db3.query(__import__('backend').models_db.ScheduledRoboticTask).filter_by(id=t.id).first()
                            crud.update_scheduled_task_status(db3, t3, 'completed', assigned_robot_id=assigned_robot)
                            logger.info("Task %s completed", t.task_id)
                            if sio:
                                payload = {'task_id': t.task_id, 'status': 'completed', 'assigned_robot_id': assigned_robot, 'tenant_id': t.tenant_id, 'timestamp': datetime.utcnow().isoformat()}
                                asyncio.create_task(sio.emit('robot:task_update', payload))
                        except Exception:
                            logger.exception("Failed to complete %s", t.task_id)

        except Exception:
            logger.exception("Error in robot_task_worker main loop")

        await asyncio.sleep(poll_interval)
