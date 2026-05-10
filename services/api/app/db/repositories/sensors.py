"""Sensor repository: register-on-first-sight + read."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Sensor


class SensorsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert(
        self,
        *,
        sensor_id: str,
        device_id: str,
        metric: str,
        unit: str,
        topic: str,
    ) -> None:
        """Register the sensor on first sight; do nothing if it already exists."""
        now = datetime.now(timezone.utc)
        stmt = (
            sqlite_insert(Sensor)
            .values(
                id=sensor_id,
                device_id=device_id,
                metric=metric,
                unit=unit,
                topic=topic,
                created_at=now,
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        await self.session.execute(stmt)

    async def get(self, sensor_id: str) -> Sensor | None:
        return await self.session.get(Sensor, sensor_id)

    async def list_all(self) -> list[Sensor]:
        result = await self.session.scalars(select(Sensor).order_by(Sensor.id))
        return list(result.all())
