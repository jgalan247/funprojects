"""Audit log repository: structured platform events.

Used by the retention job, the AI service (Phase 6), and any operator-visible
event we want to surface in the dashboard. Not a stand-in for stdout logs.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SystemLog


class SystemLogsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def write(
        self,
        *,
        level: str,
        source: str,
        event: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        self.session.add(
            SystemLog(
                ts=datetime.now(timezone.utc),
                level=level,
                source=source,
                event=event,
                detail_json=json.dumps(detail or {}, default=str),
            )
        )

    async def latest(self, limit: int = 100) -> list[SystemLog]:
        stmt = select(SystemLog).order_by(SystemLog.ts.desc()).limit(limit)
        result = await self.session.scalars(stmt)
        return list(result.all())
