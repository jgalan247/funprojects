"""Device repository: idempotent upsert + read."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Device


class DevicesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_seen(self, device_id: str, kind: str = "unknown") -> None:
        """Insert if new, otherwise bump ``last_seen_at``."""
        now = datetime.now(timezone.utc)
        stmt = (
            sqlite_insert(Device)
            .values(
                id=device_id,
                display_name=device_id,
                kind=kind,
                metadata_json="{}",
                created_at=now,
                last_seen_at=now,
            )
            .on_conflict_do_update(
                index_elements=["id"],
                set_={"last_seen_at": now},
            )
        )
        await self.session.execute(stmt)

    async def get(self, device_id: str) -> Device | None:
        return await self.session.get(Device, device_id)

    async def list_all(self) -> list[Device]:
        result = await self.session.scalars(select(Device).order_by(Device.id))
        return list(result.all())
