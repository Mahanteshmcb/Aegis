from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.services import broadcast

router = APIRouter()


@router.get("/api/v1/stream/events")
async def stream_events(request: Request):
    q = broadcast.subscribe()

    async def event_generator():
        try:
            while True:
                # disconnect check
                if await request.is_disconnected():
                    break
                data = await q.get()
                yield f"data: {data}\n\n"
        finally:
            broadcast.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
