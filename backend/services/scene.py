"""Services for scene entity management and realtime broadcasting."""
from typing import Dict, Any
from backend import realtime


async def broadcast_entity_update(entity: Dict[str, Any]):
    """Broadcast a single entity update to realtime clients."""
    try:
        await realtime.sio.emit("scene:entity_update", entity)
    except Exception:
        # Best-effort broadcast; don't fail the request if realtime is unavailable
        realtime.logger.exception("Failed to broadcast scene entity update")
