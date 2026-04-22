"""add bookings reserved_until for pending holds

Revision ID: f2a9b3c1d0e1
Revises: d1a2b3c4d5e6
Create Date: 2026-04-22
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a9b3c1d0e1"
down_revision: Union[str, Sequence[str], None] = "d1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column("reserved_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "idx_bookings_reserved_until",
        "bookings",
        ["reserved_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_bookings_reserved_until", table_name="bookings")
    op.drop_column("bookings", "reserved_until")
