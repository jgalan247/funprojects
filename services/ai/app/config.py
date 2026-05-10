"""Settings — env vars only. Loaded lazily so missing values surface as
KeyError at first use rather than at import time."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str | None
    anthropic_model: str
    anthropic_max_output_tokens: int
    anthropic_timeout_s: int
    db_path: str

    @property
    def has_api_key(self) -> bool:
        return bool(self.anthropic_api_key)


def load() -> Settings:
    return Settings(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001"),
        anthropic_max_output_tokens=int(
            os.environ.get("ANTHROPIC_MAX_OUTPUT_TOKENS", "256")
        ),
        anthropic_timeout_s=int(os.environ.get("ANTHROPIC_TIMEOUT_S", "15")),
        db_path=os.environ.get("DB_PATH", "/data/sqlite/platform.db"),
    )
