"""Anonymize soft-deleted user PII.

Revision ID: 016_anonymize_deleted_user_pii
Revises: 015_order_checkout_session_id
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "016_anonymize_deleted_user_pii"
down_revision: str | Sequence[str] | None = "015_order_checkout_session_id"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Allow deleted users to drop PII and release their original email."""
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(length=100),
        nullable=True,
    )
    op.execute(
        sa.text(
            """
            UPDATE users
            SET
                email = 'deleted+' || CAST(id AS VARCHAR) || '@deleted.local',
                name = NULL,
                phone = NULL
            WHERE deleted_at IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    """Restore non-null user names."""
    op.execute(sa.text("UPDATE users SET name = 'Deleted user' WHERE name IS NULL"))
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(length=100),
        nullable=False,
    )
