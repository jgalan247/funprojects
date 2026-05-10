"""FastAPI app entry point.

Phase 4: persistence is real. The lifespan handler now:
  - opens an async SQLite engine (WAL mode, FK enforcement),
  - runs Alembic ``upgrade head`` once,
  - hydrates the in-memory cache from the database so the dashboard sees
    the last-known reading per sensor on startup,
  - starts the MQTT subscriber,
  - schedules the nightly retention job.

``on_reading`` is the join point: cache update → DB upsert/append →
WebSocket broadcast.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import sensors as sensors_api
from app.api import system as system_api
from app.db.engine import make_engine, make_sessionmaker
from app.db.migrate import upgrade_head
from app.db.repositories.devices import DevicesRepository
from app.db.repositories.readings import ReadingsRepository
from app.db.repositories.sensors import SensorsRepository
from app.db.repositories.system_logs import SystemLogsRepository
from app.jobs import retention as retention_job
from app.mqtt.client import run_subscriber
from app.state import LatestReadingsStore, Reading, reading_to_dict
from app.ws import sensors as sensors_ws
from app.ws.manager import ConnectionManager

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("iot.api")


async def hydrate_cache(SessionLocal, store: LatestReadingsStore) -> None:
    """Populate the in-memory store from the latest reading per sensor."""
    async with SessionLocal() as session:
        sensors = await SensorsRepository(session).list_all()
        latest = await ReadingsRepository(session).latest_per_sensor()

    for sensor in sensors:
        row = latest.get(sensor.id)
        if row is None:
            continue
        store.put(
            Reading(
                sensor_id=sensor.id,
                device_id=sensor.device_id,
                metric=sensor.metric,
                value=row.value,
                unit=sensor.unit,
                quality=row.quality,
                ts=row.ts,
                # We don't store received_at; use ts so staleness reflects
                # the publisher's clock. Cards will show STALE on restart,
                # which is correct — we haven't seen anything since the
                # boot.
                received_at=row.ts,
                topic=sensor.topic,
            )
        )
    logger.info("cache hydrated: %d sensor(s)", len(store.list_all()))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Database
    await asyncio.to_thread(upgrade_head)
    engine = make_engine()
    SessionLocal = make_sessionmaker(engine)
    app.state.engine = engine
    app.state.SessionLocal = SessionLocal

    # 2. In-memory cache + WebSocket fanout
    store = LatestReadingsStore()
    manager = ConnectionManager()
    app.state.store = store
    app.state.manager = manager
    await hydrate_cache(SessionLocal, store)

    # Audit the boot — gives students a "yes, the API restarted" signal in
    # system_logs.
    async with SessionLocal() as session:
        async with session.begin():
            await SystemLogsRepository(session).write(
                level="info",
                source="api",
                event="boot",
                detail={
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "cache_size": len(store.list_all()),
                },
            )

    # 3. on_reading: cache → DB → broadcast
    async def on_reading(reading: Reading) -> None:
        store.put(reading)
        async with SessionLocal() as session:
            async with session.begin():
                await DevicesRepository(session).upsert_seen(reading.device_id)
                await SensorsRepository(session).upsert(
                    sensor_id=reading.sensor_id,
                    device_id=reading.device_id,
                    metric=reading.metric,
                    unit=reading.unit,
                    topic=reading.topic,
                )
                await ReadingsRepository(session).append(
                    sensor_id=reading.sensor_id,
                    ts=reading.ts,
                    value=reading.value,
                    quality=reading.quality,
                )
        await manager.broadcast(
            json.dumps({"type": "reading", "reading": reading_to_dict(reading)})
        )

    # 4. MQTT subscriber
    mqtt_user = os.environ.get("MQTT_USER", "")
    mqtt_password = os.environ.get("MQTT_PASSWORD", "")
    if not mqtt_user or not mqtt_password:
        logger.warning(
            "MQTT_USER / MQTT_PASSWORD not set — subscriber will not start"
        )
        mqtt_task: asyncio.Task | None = None
    else:
        mqtt_task = asyncio.create_task(
            run_subscriber(
                host=os.environ.get("MQTT_HOST", "mosquitto"),
                port=int(os.environ.get("MQTT_PORT", "1883")),
                user=mqtt_user,
                password=mqtt_password,
                on_reading=on_reading,
            ),
            name="mqtt-subscriber",
        )

    # 5. Retention scheduler — 03:00 UTC daily.
    retention_days = int(os.environ.get("READINGS_RETENTION_DAYS", "30"))
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        retention_job.run,
        CronTrigger(hour=3, minute=0),
        args=[SessionLocal, retention_days],
        id="readings-retention",
        replace_existing=True,
    )
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("retention scheduled at 03:00 UTC, %d-day window", retention_days)

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        if mqtt_task is not None:
            mqtt_task.cancel()
            try:
                await mqtt_task
            except asyncio.CancelledError:
                pass
        await engine.dispose()


app = FastAPI(title="Pi IoT Platform API", version="0.4.0", lifespan=lifespan)

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
app.include_router(system_api.router, prefix="/api")
app.include_router(sensors_ws.router)
