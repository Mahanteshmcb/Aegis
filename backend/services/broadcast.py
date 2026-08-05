"""Simple in-memory broadcaster for Server-Sent Events (SSE).

Clients call `subscribe()` to receive an `asyncio.Queue` and
`unsubscribe()` when done. Publishers `await publish(event_dict)`
to send events to all subscribers.
"""
import asyncio
import json
from typing import Set

_subscribers: Set[asyncio.Queue] = set()

def subscribe() -> asyncio.Queue:
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.add(q)
    return q

def unsubscribe(q: asyncio.Queue):
    try:
        _subscribers.discard(q)
    except Exception:
        pass

async def publish(event: dict):
    data = json.dumps(event, default=str)
    to_remove = []
    for q in list(_subscribers):
        try:
            await q.put(data)
        except Exception:
            to_remove.append(q)
    for q in to_remove:
        _subscribers.discard(q)
