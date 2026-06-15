"""Add guest_phone to orders for guest contact symmetry with bookings.

Revision ID: 008_order_guest_phone
Revises: 007_rename_slot_fk_constraints
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_order_guest_phone"
down_revision: Union[str, Sequence[str], None] = "007_rename_slot_fk_constraints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Persist guest phone on course orders."""
    op.add_column(
        "orders",
        sa.Column("guest_phone", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    """Remove guest phone from orders."""
    op.drop_column("orders", "guest_phone")
