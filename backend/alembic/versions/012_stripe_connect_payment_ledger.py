"""Add Stripe Connect fields and payment ledger.

Revision ID: 012_stripe_connect_ledger
Revises: 011_instructors_attendance
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "012_stripe_connect_ledger"
down_revision: str | Sequence[str] | None = "011_instructors_attendance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Add Connect state and local payment/refund ledger tables."""
    op.add_column("studios", sa.Column("stripe_account_id", sa.String(255), nullable=True))
    op.add_column(
        "studios",
        sa.Column("stripe_charges_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "studios",
        sa.Column("stripe_payouts_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("studios", sa.Column("stripe_onboarding_completed_at", TZDT, nullable=True))
    op.add_column("studios", sa.Column("stripe_onboarding_url_expires_at", TZDT, nullable=True))
    op.create_index("ix_studios_stripe_account_id", "studios", ["stripe_account_id"])

    op.add_column("orders", sa.Column("application_fee_cents", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("payment_intent_id", sa.String(255), nullable=True))
    op.create_index("ix_orders_payment_intent_id", "orders", ["payment_intent_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("booking_id", sa.Integer(), sa.ForeignKey("bookings.id"), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("stripe_checkout_session_id", sa.String(255), nullable=False),
        sa.Column("stripe_payment_intent_id", sa.String(255), nullable=True),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(30), nullable=False, server_default="stripe"),
        sa.Column("paid_at", TZDT, nullable=True),
        sa.Column("refunded_amount_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "(booking_id IS NOT NULL) <> (order_id IS NOT NULL)",
            name="ck_payments_exactly_one_parent",
        ),
    )
    op.create_index("ix_payments_id", "payments", ["id"])
    op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
    op.create_index("ix_payments_order_id", "payments", ["order_id"])
    op.create_index(
        "ix_payments_stripe_checkout_session_id",
        "payments",
        ["stripe_checkout_session_id"],
        unique=True,
    )
    op.create_index("ix_payments_stripe_payment_intent_id", "payments", ["stripe_payment_intent_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_provider", "payments", ["provider"])
    op.create_index("ix_payments_created_at", "payments", ["created_at"])

    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id"), nullable=False),
        sa.Column("stripe_refund_id", sa.String(255), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refunds_id", "refunds", ["id"])
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"])
    op.create_index("ix_refunds_stripe_refund_id", "refunds", ["stripe_refund_id"], unique=True)
    op.create_index("ix_refunds_idempotency_key", "refunds", ["idempotency_key"], unique=True)
    op.create_index("ix_refunds_status", "refunds", ["status"])


def downgrade() -> None:
    """Remove Connect state and local payment/refund ledger tables."""
    op.drop_index("ix_refunds_status", table_name="refunds")
    op.drop_index("ix_refunds_idempotency_key", table_name="refunds")
    op.drop_index("ix_refunds_stripe_refund_id", table_name="refunds")
    op.drop_index("ix_refunds_payment_id", table_name="refunds")
    op.drop_index("ix_refunds_id", table_name="refunds")
    op.drop_table("refunds")

    op.drop_index("ix_payments_created_at", table_name="payments")
    op.drop_index("ix_payments_provider", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_stripe_payment_intent_id", table_name="payments")
    op.drop_index("ix_payments_stripe_checkout_session_id", table_name="payments")
    op.drop_index("ix_payments_order_id", table_name="payments")
    op.drop_index("ix_payments_booking_id", table_name="payments")
    op.drop_index("ix_payments_id", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_orders_payment_intent_id", table_name="orders")
    op.drop_column("orders", "payment_intent_id")
    op.drop_column("orders", "application_fee_cents")

    op.drop_index("ix_studios_stripe_account_id", table_name="studios")
    op.drop_column("studios", "stripe_onboarding_url_expires_at")
    op.drop_column("studios", "stripe_onboarding_completed_at")
    op.drop_column("studios", "stripe_payouts_enabled")
    op.drop_column("studios", "stripe_charges_enabled")
    op.drop_column("studios", "stripe_account_id")
