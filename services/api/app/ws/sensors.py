"""WebSocket endpoint that streams sensor readings.

On connect, the client receives a snapshot of every known sensor's latest
reading. From then on, each new reading is pushed as a separate frame.

Frame shapes (JSON):
- {"type": "snapshot", "readings": [Reading, ...]}
- {"type": "reading",  "reading":  Reading}
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.state import LatestReadingsStore, reading_to_dict
from app.ws.manager import ConnectionManager

router = APIRouter()
logger = logging.getLogger("iot.ws")


@router.websocket("/ws/sensors")
async def sensors_ws(ws: WebSocket) -> None:
    store: LatestReadingsStore = ws.app.state.store
    manager: ConnectionManager = ws.app.state.manager

    await manager.connect(ws)
    try:
        snapshot = {
            "type": "snapshot",
            "readings": [reading_to_dict(r) for r in store.list_all()],
        }
        await ws.send_text(json.dumps(snapshot))

        # Keep the connection open. We don't expect inbound messages from the
        # browser; receive_text blocks until the client disconnects.
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(ws)
