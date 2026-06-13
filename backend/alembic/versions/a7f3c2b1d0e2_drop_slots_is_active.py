"""drop slots is_active column

Revision ID: a7f3c2b1d0e2
Revises: f2a9b3c1d0e1
Create Date: 2026-06-13
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7f3c2b1d0e2"
down_revision: Union[str, Sequence[str], None] = "f2a9b3c1d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE slots
        SET status = 'cancelled'
        WHERE is_active = false AND status = 'active'
        """
    )
    op.drop_column("slots", "is_active")


def downgrade() -> None:
    op.add_column(
        "slots",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.execute(
        """
        UPDATE slots
        SET is_active = (status = 'active')
        """
    )
    op.alter_column("slots", "is_active", server_default=None)
