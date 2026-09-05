import asyncio
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, AsyncGenerator

class NotificationBroadcaster:
    """Lightweight in-memory pub-sub broadcaster for Server-Sent Events (SSE)."""
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []
        self._history: List[Dict[str, Any]] = []
        self._max_history = 50

    async def subscribe(self) -> AsyncGenerator[str, None]:
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        try:
            # Yield initial connection ping
            yield f"event: connected\ndata: {json.dumps({'status': 'connected', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
            while True:
                msg = await queue.get()
                yield f"data: {json.dumps(msg)}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in self._subscribers:
                self._subscribers.remove(queue)

    async def broadcast(
        self,
        event_type: str,
        title: str,
        message: str,
        severity: str = "INFO",  # SUCCESS, WARNING, INFO, ERROR
        workflow_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        amount: Optional[float] = None
    ):
        event_data = {
            "id": f"notif_{datetime.now(timezone.utc).strftime('%H%M%S%f')}",
            "event_type": event_type,
            "title": title,
            "message": message,
            "severity": severity,
            "workflow_id": workflow_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False
        }
        
        # Keep history
        self._history.insert(0, event_data)
        if len(self._history) > self._max_history:
            self._history = self._history[:self._max_history]

        # Broadcast to all live subscribers
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(event_data)
            except asyncio.QueueFull:
                pass

    def get_history(self, limit: int = 30) -> List[Dict[str, Any]]:
        return self._history[:limit]

# Singleton instance
broadcaster = NotificationBroadcaster()
