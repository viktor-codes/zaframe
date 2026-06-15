"""Add processed_webhook_events for Stripe webhook idempotency.

Revision ID: 004_processed_webhook_events
Revises: 003_booking_expired_completed_indexes
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_processed_webhook_events"
down_revision: Union[str, Sequence[str], None] = "003_booking_expired_completed_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Ledger of processed Stripe event.id values for webhook idempotency."""
    op.create_table(
        "processed_webhook_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.String(length=255), nullable=False),
        sa.Column("type", sa.String(length=128), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_id", name="uq_processed_webhook_events_event_id"),
    )
    op.create_index(
        op.f("ix_processed_webhook_events_event_id"),
        "processed_webhook_events",
        ["event_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_processed_webhook_events_id"),
        "processed_webhook_events",
        ["id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop webhook idempotency ledger."""
    op.drop_index(op.f("ix_processed_webhook_events_id"), table_name="processed_webhook_events")
    op.drop_index(op.f("ix_processed_webhook_events_event_id"), table_name="processed_webhook_events")
    op.drop_table("processed_webhook_events")
