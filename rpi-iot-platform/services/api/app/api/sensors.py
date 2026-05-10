"""REST endpoints for sensors and their readings.

Phase 4 sources both the catalogue and the time-series from the database.
The in-memory cache is no longer queried here — it's purely a fanout
optimisation for WebSocket snapshots.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.db.repositories.readings import ReadingsRepository
from app.db.repositories.sensors import SensorsRepository

router = APIRouter()


def _sensor_summary_dict(sensor, latest) -> dict:
    return {
        "sensor_id": sensor.id,
        "device_id": sensor.device_id,
        "metric": sensor.metric,
        "unit": sensor.unit,
        "topic": sensor.topic,
        "created_at": sensor.created_at.isoformat(),
        "latest": (
            {
                "value": latest.value,
                "quality": latest.quality,
                "ts": latest.ts.isoformat(),
            }
            if latest is not None
            else None
        ),
    }


def _reading_dict(reading) -> dict:
    return {
        "ts": reading.ts.isoformat(),
        "value": reading.value,
        "quality": reading.quality,
    }


@router.get("/sensors")
async def list_sensors(request: Request) -> list[dict]:
    """Every sensor that has ever published, with its latest reading."""
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        sensors = await SensorsRepository(session).list_all()
        latest_map = await ReadingsRepository(session).latest_per_sensor()
        return [_sensor_summary_dict(s, latest_map.get(s.id)) for s in sensors]


@router.get("/sensors/{sensor_id}")
async def get_sensor(request: Request, sensor_id: str) -> dict:
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        sensor = await SensorsRepository(session).get(sensor_id)
        if sensor is None:
            raise HTTPException(404, f"sensor {sensor_id!r} not found")
        latest = await ReadingsRepository(session).latest_for_sensor(sensor_id, limit=1)
        return _sensor_summary_dict(sensor, latest[0] if latest else None)


@router.get("/sensors/{sensor_id}/readings")
async def list_readings(
    request: Request,
    sensor_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    """Most recent ``limit`` readings for a sensor, newest first."""
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        sensor = await SensorsRepository(session).get(sensor_id)
        if sensor is None:
            raise HTTPException(404, f"sensor {sensor_id!r} not found")
        readings = await ReadingsRepository(session).latest_for_sensor(
            sensor_id, limit=limit
        )
        return [_reading_dict(r) for r in readings]
