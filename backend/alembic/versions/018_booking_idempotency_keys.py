"""Idempotency ledger for POST /bookings create retries.

Revision ID: 018_booking_idempotency_keys
Revises: 017_booking_guest_email_ci_unique
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "018_booking_idempotency_keys"
down_revision: str | Sequence[str] | None = "017_booking_guest_email_ci_unique"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "booking_idempotency_keys",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("request_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("resource_kind", sa.String(length=20), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_booking_idempotency_keys_key"),
    )
    op.create_index(
        "ix_booking_idempotency_keys_idempotency_key",
        "booking_idempotency_keys",
        ["idempotency_key"],
        unique=False,
    )
    op.create_index(
        "ix_booking_idempotency_keys_expires_at",
        "booking_idempotency_keys",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_idempotency_keys_expires_at",
        table_name="booking_idempotency_keys",
    )
    op.drop_index(
        "ix_booking_idempotency_keys_idempotency_key",
        table_name="booking_idempotency_keys",
    )
    op.drop_table("booking_idempotency_keys")
