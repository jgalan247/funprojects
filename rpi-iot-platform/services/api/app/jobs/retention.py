"""Reading retention.

Daily job that deletes ``sensor_readings`` rows older than ``retention_days``
and writes an audit row to ``system_logs`` so the operation is observable.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.db.repositories.readings import ReadingsRepository
from app.db.repositories.system_logs import SystemLogsRepository

logger = logging.getLogger("iot.jobs.retention")


async def run(
    SessionLocal: async_sessionmaker[AsyncSession],
    retention_days: int,
) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    async with SessionLocal() as session:
        async with session.begin():
            deleted = await ReadingsRepository(session).delete_older_than(cutoff)
            await SystemLogsRepository(session).write(
                level="info",
                source="retention",
                event="reading_retention.run",
                detail={
                    "deleted": deleted,
                    "cutoff": cutoff.isoformat(),
                    "retention_days": retention_days,
                },
            )
    logger.info(
        "retention deleted %d readings older than %s", deleted, cutoff.isoformat()
    )
