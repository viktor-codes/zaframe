"""studios_amenities_jsonb

Revision ID: c4e8b2a1903f
Revises: ba2c1fa16678
Create Date: 2026-02-13 (amenities json -> jsonb for @> operator)

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c4e8b2a1903f"
down_revision: Union[str, Sequence[str], None] = "ba2c1fa16678"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE studios ALTER COLUMN amenities TYPE jsonb USING amenities::jsonb"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE studios ALTER COLUMN amenities TYPE json USING amenities::json"
    )
