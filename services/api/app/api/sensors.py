"""REST endpoints for the latest known sensor readings."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.state import LatestReadingsStore, reading_to_dict

router = APIRouter()


@router.get("/sensors")
async def list_sensors(request: Request) -> list[dict]:
    store: LatestReadingsStore = request.app.state.store
    readings = sorted(store.list_all(), key=lambda r: r.sensor_id)
    return [reading_to_dict(r) for r in readings]


@router.get("/sensors/{sensor_id}")
async def get_sensor(request: Request, sensor_id: str) -> dict:
    store: LatestReadingsStore = request.app.state.store
    reading = store.get(sensor_id)
    if reading is None:
        raise HTTPException(status_code=404, detail=f"sensor {sensor_id!r} not found")
    return reading_to_dict(reading)
