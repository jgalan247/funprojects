"""Sensor-readings repository: append, read by sensor, retention delete."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SensorReading


class ReadingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def append(
        self,
        *,
        sensor_id: str,
        ts: datetime,
        value: float,
        quality: str = "good",
    ) -> None:
        self.session.add(
            SensorReading(sensor_id=sensor_id, ts=ts, value=value, quality=quality)
        )

    async def latest_for_sensor(
        self, sensor_id: str, limit: int = 50
    ) -> list[SensorReading]:
        stmt = (
            select(SensorReading)
            .where(SensorReading.sensor_id == sensor_id)
            .order_by(SensorReading.ts.desc())
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return list(result.all())

    async def latest_per_sensor(self) -> dict[str, SensorReading]:
        """One reading per sensor — the most recent. Used to hydrate the
        in-memory cache on startup."""
        result = await self.session.scalars(
            select(SensorReading).order_by(
                SensorReading.sensor_id, SensorReading.ts.desc()
            )
        )
        latest: dict[str, SensorReading] = {}
        for row in result.all():
            latest.setdefault(row.sensor_id, row)
        return latest

    async def delete_older_than(self, cutoff: datetime) -> int:
        result = await self.session.execute(
            delete(SensorReading).where(SensorReading.ts < cutoff)
        )
        return int(result.rowcount or 0)
