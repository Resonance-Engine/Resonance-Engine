"""Create events, signals, and entities tables.

Revision ID: 001_initial
Revises: None
Create Date: 2026-04-05
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Events table ---
    op.create_table(
        "events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(16), nullable=False),
        sa.Column("entities", postgresql.JSONB(), server_default="[]"),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_events_timestamp", "events", ["timestamp"])
    op.create_index("ix_events_timestamp_desc", "events", [sa.text("timestamp DESC")])
    op.create_index("ix_events_content_hash", "events", ["content_hash"])
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index(
        "ix_events_entities_gin",
        "events",
        ["entities"],
        postgresql_using="gin",
    )

    # --- Signals table ---
    op.create_table(
        "signals",
        sa.Column("signal_id", sa.String(), primary_key=True),
        sa.Column("event_id", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(), nullable=False),
        sa.Column("signal_type", sa.String(), nullable=False),
        sa.Column("signal_text", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("uncertainty", sa.Text(), nullable=False),
        sa.Column("impact_window", sa.String(), nullable=False),
        sa.Column("predicted_move", sa.Float(), nullable=True),
        sa.Column("actual_move", sa.Float(), nullable=True),
        sa.Column("evidence", postgresql.JSONB(), server_default="[]"),
        sa.Column("citations", postgresql.JSONB(), server_default="[]"),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_signals_event_id", "signals", ["event_id"])
    op.create_index("ix_signals_timestamp", "signals", ["timestamp"])
    op.create_index("ix_signals_timestamp_desc", "signals", [sa.text("timestamp DESC")])
    op.create_index("ix_signals_ticker", "signals", ["ticker"])

    # --- Entities table ---
    op.create_table(
        "entities",
        sa.Column("ticker", sa.String(), primary_key=True),
        sa.Column("cik", sa.String(), unique=True, nullable=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sic_code", sa.String(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("entities")
    op.drop_table("signals")
    op.drop_table("events")
