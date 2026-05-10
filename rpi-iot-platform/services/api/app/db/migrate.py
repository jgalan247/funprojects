"""Run Alembic ``upgrade head`` synchronously.

Called from the FastAPI lifespan handler via :func:`asyncio.to_thread` on
boot. Idempotent — Alembic does nothing if the database is already at head.
"""
from __future__ import annotations

import os

from alembic import command
from alembic.config import Config

from app.db.engine import db_url_sync


def _config() -> Config:
    here = os.path.dirname(os.path.abspath(__file__))
    cfg = Config()
    cfg.set_main_option("script_location", os.path.join(here, "migrations"))
    cfg.set_main_option("sqlalchemy.url", db_url_sync())
    return cfg


def upgrade_head() -> None:
    db = db_url_sync().removeprefix("sqlite:///")
    os.makedirs(os.path.dirname(db) or ".", exist_ok=True)
    command.upgrade(_config(), "head")
