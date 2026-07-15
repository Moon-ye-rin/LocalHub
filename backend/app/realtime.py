"""In-process WebSocket notification and presence manager.

The project runs with a single Render worker by default. When scaling to multiple
workers, replace this in-memory broadcaster with Redis pub/sub.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class RealtimeManager:
    def __init__(self) -> None:
        self._connections: dict[WebSocket, str] = {}

    @property
    def online_count(self) -> int:
        return len(set(self._connections.values()))

    async def connect(self, websocket: WebSocket, client_key: str) -> None:
        await websocket.accept()
        self._connections[websocket] = client_key or f"socket-{id(websocket)}"
        await self._send(websocket, {
            "type": "connected",
            "online_count": self.online_count,
            "server_time": datetime.now(timezone.utc).isoformat(),
        })
        await self.broadcast_presence()

    async def disconnect(self, websocket: WebSocket) -> None:
        self._connections.pop(websocket, None)
        await self.broadcast_presence()

    async def _send(self, websocket: WebSocket, payload: dict[str, Any]) -> bool:
        try:
            await websocket.send_json(payload)
            return True
        except Exception:
            self._connections.pop(websocket, None)
            return False

    async def broadcast(self, payload: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for websocket in list(self._connections):
            if not await self._send(websocket, payload):
                stale.append(websocket)
        for websocket in stale:
            self._connections.pop(websocket, None)

    async def broadcast_presence(self) -> None:
        await self.broadcast({"type": "presence", "online_count": self.online_count})

    async def publish_post_created(
        self,
        *,
        post_id: int,
        title: str,
        category: str,
        region: str,
        district: str,
    ) -> None:
        await self.broadcast({
            "type": "post_created",
            "post": {
                "id": post_id,
                "title": title,
                "category": category,
                "region": region,
                "district": district,
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
        })


realtime_manager = RealtimeManager()
