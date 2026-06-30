"""Add checkout session id to orders.

Revision ID: 015_order_checkout_session_id
Revises: 014_catalog_product_lifecycle
Create Date: 2026-06-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "015_order_checkout_session_id"
down_revision: str | Sequence[str] | None = "014_catalog_product_lifecycle"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Persist Stripe Checkout Session id on orders."""
    op.add_column("orders", sa.Column("checkout_session_id", sa.String(255), nullable=True))
    op.create_index("ix_orders_checkout_session_id", "orders", ["checkout_session_id"])


def downgrade() -> None:
    """Remove Stripe Checkout Session id from orders."""
    op.drop_index("ix_orders_checkout_session_id", table_name="orders")
    op.drop_column("orders", "checkout_session_id")
