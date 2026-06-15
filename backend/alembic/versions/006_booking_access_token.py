"""Add guest checkout access tokens to bookings and orders.

Revision ID: 006_booking_access_token
Revises: 005_domain_vocabulary
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_booking_access_token"
down_revision: Union[str, Sequence[str], None] = "005_domain_vocabulary"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add access_token columns for guest checkout authorization."""
    op.add_column(
        "bookings",
        sa.Column("access_token", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_bookings_access_token", "bookings", ["access_token"])

    op.add_column(
        "orders",
        sa.Column("access_token", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_orders_access_token", "orders", ["access_token"])


def downgrade() -> None:
    """Remove guest checkout access token columns."""
    op.drop_index("ix_orders_access_token", table_name="orders")
    op.drop_column("orders", "access_token")

    op.drop_index("ix_bookings_access_token", table_name="bookings")
    op.drop_column("bookings", "access_token")
