"""Snapshot repository — capture + read."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Snapshot


class SnapshotsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def take(
        self, *, label: str | None, readings: list[dict[str, Any]]
    ) -> Snapshot:
        snapshot = Snapshot(
            taken_at=datetime.now(timezone.utc),
            label=label,
            readings_json=json.dumps(readings, default=str),
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def list_recent(self, limit: int = 50) -> list[Snapshot]:
        stmt = select(Snapshot).order_by(Snapshot.taken_at.desc()).limit(limit)
        return list((await self.session.scalars(stmt)).all())

    async def get(self, snapshot_id: int) -> Snapshot | None:
        return await self.session.get(Snapshot, snapshot_id)
