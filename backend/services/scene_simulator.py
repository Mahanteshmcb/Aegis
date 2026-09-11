"""Simple simulator that nudges scene entities and broadcasts updates.

Provides runtime control helpers: `pause_simulation`, `resume_simulation`, and
`is_running` so external APIs or the admin UI can control the simulator.
"""
import asyncio
import random
import logging
from typing import Literal

from backend.database import SessionLocal
from backend import models_scene as models
from backend.services import scene as scene_service

logger = logging.getLogger(__name__)

# Global control flag for the simulator
_running = True
# Tick delay in seconds between simulation steps (lower = faster)
_tick_seconds = 1.0


def pause_simulation():
    global _running
    _running = False


def resume_simulation():
    global _running
    _running = True


def is_running() -> bool:
    return bool(_running)


def set_tick_seconds(sec: float):
    global _tick_seconds
    try:
        sec = float(sec)
    except Exception:
        return False
    if sec <= 0:
        return False
    _tick_seconds = sec
    return True


def get_tick_seconds() -> float:
    return float(_tick_seconds)


async def scene_entity_mover():
    try:
        while True:
            await asyncio.sleep(_tick_seconds)
            if not is_running():
                continue
            try:
                with SessionLocal() as db:
                    rows = db.query(models.SceneEntity).all()
                    if not rows:
                        continue
                    ent = random.choice(rows)
                    # small random walk with configurable magnitude
                    ent.x += random.uniform(-0.3, 0.3)
                    ent.y += random.uniform(-0.3, 0.3)
                    ent.rotation = (ent.rotation + random.uniform(-8, 8)) % 360
                    db.add(ent)
                    db.commit()
                    db.refresh(ent)
                    payload = {
                        "id": ent.id,
                        "name": ent.name,
                        "type": ent.type,
                        "model": ent.model,
                        "x": ent.x,
                        "y": ent.y,
                        "z": ent.z,
                        "rotation": ent.rotation,
                        "state": ent.state or {},
                    }
                    try:
                        await scene_service.broadcast_entity_update(payload)
                    except Exception:
                        logger.exception("Failed to broadcast moved entity")
            except Exception:
                logger.exception("scene_entity_mover loop error")
    except asyncio.CancelledError:
        logger.info("scene_entity_mover cancelled")
