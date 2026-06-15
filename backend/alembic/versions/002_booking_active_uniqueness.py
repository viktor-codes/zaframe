"""Add partial unique indexes for active bookings per slot and guest.

Revision ID: 002_booking_active_uniqueness
Revises: 001_initial
Create Date: 2026-06-15

WHY: one guest (email or user_id) must not hold multiple non-cancelled bookings
on the same slot; DB enforces under concurrent inserts.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_booking_active_uniqueness"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ACTIVE_WHERE = "status != 'cancelled'"


def upgrade() -> None:
    """Enforce at most one active booking per (slot, guest_email) and (slot, user_id)."""
    op.create_index(
        "uq_bookings_slot_guest_email_active",
        "bookings",
        ["slot_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND guest_email IS NOT NULL"),
    )
    op.create_index(
        "uq_bookings_slot_user_id_active",
        "bookings",
        ["slot_id", "user_id"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND user_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Drop active-booking uniqueness indexes."""
    op.drop_index("uq_bookings_slot_user_id_active", table_name="bookings")
    op.drop_index("uq_bookings_slot_guest_email_active", table_name="bookings")
