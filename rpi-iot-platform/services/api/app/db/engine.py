"""Async SQLAlchemy engine and sessionmaker factory.

WAL mode and foreign-key enforcement are set on every new SQLite connection
via the sync side of the async engine.
"""
from __future__ import annotations

import os

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def db_path() -> str:
    return os.environ.get("DB_PATH", "/data/sqlite/platform.db")


def db_url_async() -> str:
    return f"sqlite+aiosqlite:///{db_path()}"


def db_url_sync() -> str:
    """Used by Alembic, which is sync."""
    return f"sqlite:///{db_path()}"


def make_engine() -> AsyncEngine:
    engine = create_async_engine(db_url_async(), echo=False, future=True)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record) -> None:  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

    return engine


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
