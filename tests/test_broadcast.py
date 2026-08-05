import asyncio
from backend.services import broadcast


def test_subscribe_publish_event_loop():
    q = broadcast.subscribe()
    try:
        async def runner():
            await broadcast.publish({"type": "test", "payload": 123})
            val = await q.get()
            assert '"type": "test"' in val
        asyncio.get_event_loop().run_until_complete(runner())
    finally:
        broadcast.unsubscribe(q)
