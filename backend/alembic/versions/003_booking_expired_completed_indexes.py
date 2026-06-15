"""Tighten active-booking partial indexes for expired/completed statuses.

Revision ID: 003_booking_active_idx
Revises: 002_booking_active_uniqueness
Create Date: 2026-06-15

WHY: expired and completed bookings must not block re-booking the same slot.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_booking_active_idx"
down_revision: Union[str, Sequence[str], None] = "002_booking_active_uniqueness"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OLD_ACTIVE_WHERE = "status != 'cancelled'"
_NEW_ACTIVE_WHERE = "status IN ('pending', 'confirmed')"


def upgrade() -> None:
    """Only pending/confirmed rows participate in active-booking uniqueness."""
    op.drop_index("uq_bookings_slot_guest_email_active", table_name="bookings")
    op.drop_index("uq_bookings_slot_user_id_active", table_name="bookings")
    op.create_index(
        "uq_bookings_slot_guest_email_active",
        "bookings",
        ["slot_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(f"{_NEW_ACTIVE_WHERE} AND guest_email IS NOT NULL"),
    )
    op.create_index(
        "uq_bookings_slot_user_id_active",
        "bookings",
        ["slot_id", "user_id"],
        unique=True,
        postgresql_where=sa.text(f"{_NEW_ACTIVE_WHERE} AND user_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Restore legacy active-booking uniqueness (cancelled-only exclusion)."""
    op.drop_index("uq_bookings_slot_guest_email_active", table_name="bookings")
    op.drop_index("uq_bookings_slot_user_id_active", table_name="bookings")
    op.create_index(
        "uq_bookings_slot_guest_email_active",
        "bookings",
        ["slot_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(f"{_OLD_ACTIVE_WHERE} AND guest_email IS NOT NULL"),
    )
    op.create_index(
        "uq_bookings_slot_user_id_active",
        "bookings",
        ["slot_id", "user_id"],
        unique=True,
        postgresql_where=sa.text(f"{_OLD_ACTIVE_WHERE} AND user_id IS NOT NULL"),
    )
