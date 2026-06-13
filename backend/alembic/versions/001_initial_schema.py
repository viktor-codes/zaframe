"""Initial schema (squashed): timestamptz, studio timezone, full domain model.

Revision ID: 001_initial
Revises:
Create Date: 2026-06-12

WHY squash: greenfield rebuild per ADR-001 — single migration with TIMESTAMPTZ
and studios.timezone from day one; no incremental naive-UTC history.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

service_category_enum = postgresql.ENUM(
    "yoga",
    "boxing",
    "dance",
    "hiit",
    "pilates",
    "martial_arts",
    "strength",
    name="service_category",
    create_type=False,
)

TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Create full schema with TIMESTAMPTZ instants and studio IANA timezone."""
    bind = op.get_bind()
    service_category_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("magic_link_token", sa.String(255), nullable=True),
        sa.Column("magic_link_expires_at", TZDT, nullable=True),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", TZDT, nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jti", sa.String(64), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", TZDT, nullable=False),
        sa.Column("revoked_at", TZDT, nullable=True),
        sa.Column("last_used_at", TZDT, nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_jti", "refresh_tokens", ["jti"], unique=True)
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])
    op.create_index("ix_refresh_tokens_revoked_at", "refresh_tokens", ["revoked_at"])

    op.create_table(
        "guest_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("expires_at", TZDT, nullable=False),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_guest_sessions_id", "guest_sessions", ["id"])
    op.create_index("ix_guest_sessions_session_id", "guest_sessions", ["session_id"], unique=True)
    op.create_index("ix_guest_sessions_email", "guest_sessions", ["email"])
    op.create_index("ix_guest_sessions_expires_at", "guest_sessions", ["expires_at"])

    op.create_table(
        "studios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("amenities", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column(
            "timezone",
            sa.String(64),
            nullable=False,
            server_default="UTC",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_studios_id", "studios", ["id"])
    op.create_index("ix_studios_owner_id", "studios", ["owner_id"])
    op.create_index("ix_studios_slug", "studios", ["slug"], unique=True)
    op.create_index("ix_studios_city", "studios", ["city"])

    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("studio_id", sa.Integer(), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("category", service_category_enum, nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("price_single_cents", sa.Integer(), nullable=False),
        sa.Column("price_course_cents", sa.Integer(), nullable=True),
        sa.Column("soft_limit_ratio", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("hard_limit_ratio", sa.Float(), nullable=False, server_default="1.5"),
        sa.Column("max_overbooked_ratio", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_services_id", "services", ["id"])
    op.create_index("ix_services_studio_id", "services", ["studio_id"])
    op.create_index("ix_services_type", "services", ["type"])
    op.create_index("ix_services_category", "services", ["category"])

    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_schedules_id", "schedules", ["id"])
    op.create_index("ix_schedules_service_id", "schedules", ["service_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("studio_id", sa.Integer(), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("guest_email", sa.String(255), nullable=True),
        sa.Column("guest_name", sa.String(100), nullable=True),
        sa.Column("total_amount_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="eur"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_orders_id", "orders", ["id"])
    op.create_index("ix_orders_studio_id", "orders", ["studio_id"])
    op.create_index("ix_orders_service_id", "orders", ["service_id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    op.create_table(
        "slots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("studio_id", sa.Integer(), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("schedule_id", sa.Integer(), sa.ForeignKey("schedules.id"), nullable=True),
        sa.Column("start_time", TZDT, nullable=False),
        sa.Column("end_time", TZDT, nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("max_capacity", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("price_cents", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("course_price_cents", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_slots_id", "slots", ["id"])
    op.create_index("ix_slots_studio_id", "slots", ["studio_id"])
    op.create_index("ix_slots_service_id", "slots", ["service_id"])
    op.create_index("ix_slots_schedule_id", "slots", ["schedule_id"])
    op.create_index("ix_slots_start_time", "slots", ["start_time"])
    op.create_index("ix_slots_status", "slots", ["status"])
    op.create_index(
        "idx_slots_studio_service_start_time",
        "slots",
        ["studio_id", "service_id", "start_time"],
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slot_id", sa.Integer(), sa.ForeignKey("slots.id"), nullable=False),
        sa.Column("booking_type", sa.String(20), nullable=False, server_default="single"),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("guest_session_id", sa.String(255), nullable=True),
        sa.Column("guest_name", sa.String(100), nullable=True),
        sa.Column("guest_email", sa.String(255), nullable=True),
        sa.Column("guest_phone", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("reserved_until", TZDT, nullable=True),
        sa.Column("checkout_session_id", sa.String(255), nullable=True),
        sa.Column("payment_intent_id", sa.String(255), nullable=True),
        sa.Column("payment_status", sa.String(50), nullable=True),
        sa.Column("unit_price_cents", sa.Integer(), nullable=True),
        sa.Column("cancelled_at", TZDT, nullable=True),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookings_id", "bookings", ["id"])
    op.create_index("ix_bookings_slot_id", "bookings", ["slot_id"])
    op.create_index("ix_bookings_booking_type", "bookings", ["booking_type"])
    op.create_index("ix_bookings_service_id", "bookings", ["service_id"])
    op.create_index("ix_bookings_order_id", "bookings", ["order_id"])
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_guest_session_id", "bookings", ["guest_session_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])
    op.create_index("ix_bookings_reserved_until", "bookings", ["reserved_until"])
    op.create_index("ix_bookings_checkout_session_id", "bookings", ["checkout_session_id"])
    op.create_index("ix_bookings_payment_intent_id", "bookings", ["payment_intent_id"])
    op.create_index("ix_bookings_created_at", "bookings", ["created_at"])


def downgrade() -> None:
    """Drop all tables."""
    bind = op.get_bind()
    op.drop_table("bookings")
    op.drop_table("slots")
    op.drop_table("orders")
    op.drop_table("schedules")
    op.drop_table("services")
    op.drop_table("studios")
    op.drop_table("guest_sessions")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    service_category_enum.drop(bind, checkfirst=True)
