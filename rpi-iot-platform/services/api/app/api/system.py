"""System-facing endpoints: structured audit log."""
from __future__ import annotations

import json

from fastapi import APIRouter, Query, Request

from app.db.repositories.system_logs import SystemLogsRepository

router = APIRouter()


@router.get("/system/logs")
async def list_logs(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict]:
    """Latest ``limit`` rows from ``system_logs``, newest first.

    Includes platform boot events, retention runs, and (Phase 6) AI errors.
    """
    SessionLocal = request.app.state.SessionLocal
    async with SessionLocal() as session:
        rows = await SystemLogsRepository(session).latest(limit=limit)
        return [
            {
                "id": r.id,
                "ts": r.ts.isoformat(),
                "level": r.level,
                "source": r.source,
                "event": r.event,
                "detail": json.loads(r.detail_json) if r.detail_json else {},
            }
            for r in rows
        ]
