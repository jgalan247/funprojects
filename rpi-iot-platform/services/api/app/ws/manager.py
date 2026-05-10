"""WebSocket connection manager.

Tracks open client sockets and broadcasts text messages to all of them.
Fails closed on send errors and prunes dead sockets.
"""
from __future__ import annotations

import logging

from fastapi import WebSocket

logger = logging.getLogger("iot.ws")


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)

    async def broadcast(self, text: str) -> None:
        if not self._connections:
            return
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(text)
            except Exception as exc:  # noqa: BLE001 — broad on purpose
                logger.debug("ws send failed, will drop: %s", exc)
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)

    @property
    def count(self) -> int:
        return len(self._connections)
