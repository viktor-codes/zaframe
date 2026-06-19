"""Add minimal studio media URL fields.

Revision ID: 009_studio_media_urls
Revises: 008_order_guest_phone
Create Date: 2026-06-19
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "009_studio_media_urls"
down_revision: Union[str, Sequence[str], None] = "008_order_guest_phone"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add public logo and cover URLs to studios."""
    op.add_column("studios", sa.Column("logo_url", sa.String(length=2048), nullable=True))
    op.add_column("studios", sa.Column("cover_url", sa.String(length=2048), nullable=True))


def downgrade() -> None:
    """Remove public studio media URLs."""
    op.drop_column("studios", "cover_url")
    op.drop_column("studios", "logo_url")
