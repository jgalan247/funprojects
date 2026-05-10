"""Writes ``ai_prompts`` and ``ai_responses`` rows for every call.

Returns the generated IDs so the API layer can include them in the HTTP
response — useful for the Settings cost view to back-link.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.db import AiPrompt, AiResponse


@dataclass(frozen=True)
class PromptRecord:
    id: str
    template_id: str
    context: dict[str, Any]
    rendered_text: str


@dataclass(frozen=True)
class ResponseRecord:
    id: str
    prompt_id: str
    provider: str
    model: str
    text: str
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int | None
    status: str   # "ok" | "error" | "timeout"
    error: str | None


def new_id() -> str:
    """26-char base-32 ID. We use uuid4 hex for simplicity; ULID would be
    nicer (sortable) but adds a dependency."""
    return uuid.uuid4().hex


async def save(
    SessionLocal: async_sessionmaker[AsyncSession],
    prompt: PromptRecord,
    response: ResponseRecord,
) -> None:
    now = datetime.now(timezone.utc)
    async with SessionLocal() as session:
        async with session.begin():
            session.add(
                AiPrompt(
                    id=prompt.id,
                    template_id=prompt.template_id,
                    context_json=json.dumps(prompt.context, default=str),
                    rendered_text=prompt.rendered_text,
                    created_at=now,
                )
            )
            session.add(
                AiResponse(
                    id=response.id,
                    prompt_id=response.prompt_id,
                    provider=response.provider,
                    model=response.model,
                    text=response.text,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    latency_ms=response.latency_ms,
                    status=response.status,
                    error=response.error,
                    created_at=now,
                )
            )
