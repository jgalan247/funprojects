"""Snapshot endpoints — capture + browse.

Captures the in-memory cache rather than re-querying the database. The
cache is the same view the dashboard sees, so a snapshot reflects the
state of the room at the exact moment the student tapped the button.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.db.repositories.snapshots import SnapshotsRepository
from app.state import reading_to_dict

router = APIRouter()
logger = logging.getLogger("iot.api.snapshots")


class SnapshotRequest(BaseModel):
    label: str | None = Field(default=None, max_length=200)


@router.post("/snapshots")
async def take_snapshot(request: Request, body: SnapshotRequest) -> dict:
    store = request.app.state.store
    SessionLocal = request.app.state.SessionLocal

    readings = [reading_to_dict(r) for r in store.list_all()]

    async with SessionLocal() as session:
        async with session.begin():
            snapshot = await SnapshotsRepository(session).take(
                label=body.label, readings=readings
            )

    return {
        "id": snapshot.id,
        "taken_at": snapshot.taken_at.isoformat(),
        "label": snapshot.label,
        "count": len(readings),
    }


@router.get("/snapshots")
async def list_snapshots(
    request: Request, limit: int = Query(default=20, ge=1, le=200)
) -> list[dict]:
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        rows = await SnapshotsRepository(session).list_recent(limit=limit)
        return [
            {
                "id": s.id,
                "taken_at": s.taken_at.isoformat(),
                "label": s.label,
                "count": len(json.loads(s.readings_json)),
            }
            for s in rows
        ]


@router.get("/snapshots/{snapshot_id}")
async def get_snapshot(request: Request, snapshot_id: int) -> dict:
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        snapshot = await SnapshotsRepository(session).get(snapshot_id)
        if snapshot is None:
            raise HTTPException(404, f"snapshot {snapshot_id} not found")
        return {
            "id": snapshot.id,
            "taken_at": snapshot.taken_at.isoformat(),
            "label": snapshot.label,
            "readings": json.loads(snapshot.readings_json),
        }
