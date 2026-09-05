from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any

from app.core.notifications import broadcaster

router = APIRouter(prefix="/events", tags=["Real-Time Notifications"])

@router.get("/stream")
async def stream_recovery_events():
    """Server-Sent Events (SSE) stream for live recovery notifications."""
    return StreamingResponse(
        broadcaster.subscribe(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/history")
async def get_notification_history(limit: int = Query(30, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Returns recent in-memory notification events."""
    return broadcaster.get_history(limit=limit)
