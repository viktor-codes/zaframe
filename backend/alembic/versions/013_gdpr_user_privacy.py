"""Add user privacy fields for GDPR minimum contract.

Revision ID: 013_gdpr_user_privacy
Revises: 012_stripe_connect_ledger
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "013_gdpr_user_privacy"
down_revision: str | Sequence[str] | None = "012_stripe_connect_ledger"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Add account privacy fields used by frontend account settings."""
    op.add_column(
        "users",
        sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("users", sa.Column("deleted_at", TZDT, nullable=True))
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])


def downgrade() -> None:
    """Remove account privacy fields."""
    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_column("users", "deleted_at")
    op.drop_column("users", "marketing_consent")
