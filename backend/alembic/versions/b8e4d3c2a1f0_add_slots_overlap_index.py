"""add composite index for slot overlap queries

Revision ID: b8e4d3c2a1f0
Revises: a7f3c2b1d0e2
Create Date: 2026-06-13
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b8e4d3c2a1f0"
down_revision: Union[str, Sequence[str], None] = "a7f3c2b1d0e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_slots_studio_service_start_time",
        "slots",
        ["studio_id", "service_id", "start_time"],
    )


def downgrade() -> None:
    op.drop_index("idx_slots_studio_service_start_time", table_name="slots")
