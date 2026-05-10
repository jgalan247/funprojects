"""FastAPI app entry point.

Wires the in-memory store, WebSocket manager, and MQTT subscriber together
under a lifespan handler so the subscriber starts on boot and is cancelled
cleanly on shutdown.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import sensors as sensors_api
from app.mqtt.client import run_subscriber
from app.state import LatestReadingsStore, Reading, reading_to_dict
from app.ws import sensors as sensors_ws
from app.ws.manager import ConnectionManager

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("iot.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = LatestReadingsStore()
    manager = ConnectionManager()
    app.state.store = store
    app.state.manager = manager

    async def on_reading(reading: Reading) -> None:
        await manager.broadcast(
            json.dumps({"type": "reading", "reading": reading_to_dict(reading)})
        )

    mqtt_user = os.environ.get("MQTT_USER", "")
    mqtt_password = os.environ.get("MQTT_PASSWORD", "")
    if not mqtt_user or not mqtt_password:
        logger.warning(
            "MQTT_USER / MQTT_PASSWORD not set — subscriber will not start"
        )
        task: asyncio.Task | None = None
    else:
        task = asyncio.create_task(
            run_subscriber(
                host=os.environ.get("MQTT_HOST", "mosquitto"),
                port=int(os.environ.get("MQTT_PORT", "1883")),
                user=mqtt_user,
                password=mqtt_password,
                store=store,
                on_reading=on_reading,
            ),
            name="mqtt-subscriber",
        )

    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


app = FastAPI(title="Pi IoT Platform API", version="0.3.0", lifespan=lifespan)

# Permissive CORS for development — the production frontend lives on the same
# origin (nginx reverse-proxies /api/* and /ws/*) so this is mainly for direct
# access from a laptop during demos.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(sensors_api.router, prefix="/api")
app.include_router(sensors_ws.router)
