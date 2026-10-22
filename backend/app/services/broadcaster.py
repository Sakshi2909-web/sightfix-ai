import asyncio
import json
from typing import Dict, List, Any


class EventBroadcaster:
    def __init__(self):
        self._listeners: Dict[str, List[asyncio.Queue]] = {}

    def subscribe(self, analysis_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if analysis_id not in self._listeners:
            self._listeners[analysis_id] = []
        self._listeners[analysis_id].append(q)
        return q

    def unsubscribe(self, analysis_id: str, q: asyncio.Queue):
        if analysis_id in self._listeners:
            try:
                self._listeners[analysis_id].remove(q)
                if not self._listeners[analysis_id]:
                    del self._listeners[analysis_id]
            except ValueError:
                pass

    async def emit(self, analysis_id: str, event_type: str, data: Dict[str, Any]):
        if analysis_id in self._listeners:
            payload = {"event": event_type, "data": data}
            for q in list(self._listeners[analysis_id]):
                await q.put(payload)


broadcaster = EventBroadcaster()
