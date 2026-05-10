"""User-triggered AI endpoints.

The API does *not* call Claude itself — it's a thin proxy:
  1. Look up the sensor's latest reading (409 if none yet).
  2. Forward to the AI service at ``$AI_URL/ai/explain``.
  3. Return the text + bookkeeping fields to the browser.

Rationale: keeps the Anthropic SDK and prompt template in one service
(easier to update independently) and means the API layer doesn't have
to know about prompt rendering.
"""
from __future__ import annotations

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.db.repositories.ai_history import AiHistoryRepository
from app.db.repositories.readings import ReadingsRepository
from app.db.repositories.sensors import SensorsRepository

router = APIRouter()
logger = logging.getLogger("iot.api.ai")

AI_URL = os.environ.get("AI_URL", "http://ai:8001")


@router.post("/ai/explain")
async def explain(request: Request, body: dict) -> dict:
    sensor_id = body.get("sensor_id")
    if not isinstance(sensor_id, str) or not sensor_id:
        raise HTTPException(400, "sensor_id is required")

    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        sensor = await SensorsRepository(session).get(sensor_id)
        if sensor is None:
            raise HTTPException(404, f"sensor {sensor_id!r} not found")
        latest = await ReadingsRepository(session).latest_for_sensor(sensor_id, limit=1)
        if not latest:
            raise HTTPException(409, "sensor has no readings yet")
        reading = latest[0]

    payload = {
        "sensor_id": sensor_id,
        "reading": {
            "source": sensor.device_id,
            "metric": sensor.metric,
            "value": reading.value,
            "unit": sensor.unit,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(f"{AI_URL}/ai/explain", json=payload)
    except httpx.HTTPError as e:
        logger.warning("AI service unreachable: %s", e)
        raise HTTPException(503, "AI service unreachable") from e

    if response.status_code != 200:
        logger.warning(
            "AI service returned %d: %s", response.status_code, response.text[:500]
        )
        raise HTTPException(502, "AI service error")

    return response.json()


@router.get("/ai/info")
async def info() -> dict:
    """Provider + model + fallback flag, surfaced to the UI banner."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{AI_URL}/ai/info")
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError:
        return {"provider": "unknown", "model": "unknown", "fallback": True}


@router.get("/ai/usage")
async def usage(request: Request, days: int = 7) -> dict:
    if days < 1 or days > 365:
        raise HTTPException(400, "days must be between 1 and 365")
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        return await AiHistoryRepository(session).usage_window(days=days)
