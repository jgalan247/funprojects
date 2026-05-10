"""SQLAlchemy ORM models. Schema mirrors docs/database-design.md §2.

All timestamps are stored as ``DateTime(timezone=True)`` and serialised by
SQLAlchemy as ISO-8601 TEXT in SQLite. Foreign keys are declared so future
backends (Postgres, Timescale) inherit them; SQLite enforcement requires
``PRAGMA foreign_keys=ON`` which is set in :mod:`app.db.engine`.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    manifest_json: Mapped[str] = mapped_column(Text, nullable=False)
    installed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    kind: Mapped[str] = mapped_column(String, nullable=False)
    module_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True
    )
    metadata_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Sensor(Base):
    __tablename__ = "sensors"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # "<device_id>.<metric>"
    device_id: Mapped[str] = mapped_column(
        String, ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    metric: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    topic: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("device_id", "metric", name="uq_sensors_device_metric"),
    )


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(
        String, ForeignKey("sensors.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[str] = mapped_column(String, default="good", nullable=False)

    __table_args__ = (
        Index("ix_sensor_readings_sensor_ts", "sensor_id", "ts"),
    )


class SystemLog(Base):
    __tablename__ = "system_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    level: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    event: Mapped[str] = mapped_column(String, nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    __table_args__ = (Index("ix_system_logs_ts", "ts"),)


class AiPrompt(Base):
    """Reserved for Phase 6 — table created in migration 0001 so we don't have
    to migrate schema again later."""

    __tablename__ = "ai_prompts"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    template_id: Mapped[str] = mapped_column(String, nullable=False)
    context_json: Mapped[str] = mapped_column(Text, nullable=False)
    rendered_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Snapshot(Base):
    """A point-in-time capture of every active sensor reading.

    Used by the classroom-sensor-hub module: students tap a button to
    freeze the current view for later discussion.
    """

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    label: Mapped[str | None] = mapped_column(Text, nullable=True)
    readings_json: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (Index("ix_snapshots_taken_at", "taken_at"),)


class AiResponse(Base):
    """Reserved for Phase 6 — see :class:`AiPrompt`."""

    __tablename__ = "ai_responses"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    prompt_id: Mapped[str] = mapped_column(
        String, ForeignKey("ai_prompts.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_ai_responses_prompt", "prompt_id"),)
