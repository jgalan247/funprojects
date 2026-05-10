"""Read-only access to ``ai_responses`` for the cost view.

Writes are owned by the AI service (see services/ai/app/persistence.py)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AiResponse


class AiHistoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def usage_window(self, days: int = 7) -> dict[str, int | None]:
        """Token totals + call counts over the last N days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        success_expr = case((AiResponse.status == "ok", 1), else_=0)
        stmt = select(
            func.count(AiResponse.id),
            func.coalesce(func.sum(AiResponse.input_tokens), 0),
            func.coalesce(func.sum(AiResponse.output_tokens), 0),
            func.coalesce(func.sum(success_expr), 0),
        ).where(AiResponse.created_at >= cutoff)

        row = (await self.session.execute(stmt)).first()
        if row is None:
            return {
                "window_days": days,
                "calls": 0,
                "successes": 0,
                "input_tokens": 0,
                "output_tokens": 0,
            }
        calls, input_tokens, output_tokens, successes = row
        return {
            "window_days": days,
            "calls": int(calls or 0),
            "successes": int(successes or 0),
            "input_tokens": int(input_tokens or 0),
            "output_tokens": int(output_tokens or 0),
        }
