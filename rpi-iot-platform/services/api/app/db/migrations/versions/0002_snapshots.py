"""snapshots — Phase 7 classroom-sensor-hub feature

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-10
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("taken_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("readings_json", sa.Text(), nullable=False),
    )
    op.create_index("ix_snapshots_taken_at", "snapshots", ["taken_at"])


def downgrade() -> None:
    # Forward-only.
    pass
