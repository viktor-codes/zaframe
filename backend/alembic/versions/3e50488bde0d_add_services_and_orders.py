"""add services and orders

Revision ID: 3e50488bde0d
Revises: 001_initial
Create Date: 2026-02-10 15:08:20.273023

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3e50488bde0d'
down_revision: Union[str, Sequence[str], None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add services, orders, schedules и новые поля."""
    # === Новые таблицы ===
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("studio_id", sa.Integer(), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.String(1000), nullable=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("max_capacity", sa.Integer(), nullable=False),
        sa.Column("price_single_cents", sa.Integer(), nullable=False),
        sa.Column("price_course_cents", sa.Integer(), nullable=True),
        sa.Column("soft_limit_ratio", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("hard_limit_ratio", sa.Float(), nullable=False, server_default="1.5"),
        sa.Column("max_overbooked_ratio", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_services_studio_id", "services", ["studio_id"])
    op.create_index("ix_services_type", "services", ["type"])

    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("service_id", sa.Integer(), sa.ForeignKey("services.id"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
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
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True,
        ),
    )
    op.create_index("ix_orders_studio_id", "orders", ["studio_id"])
    op.create_index("ix_orders_service_id", "orders", ["service_id"])
    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_status", "orders", ["status"])

    # === Изменения существующих таблиц ===
    # studios: slug
    op.add_column(
        "studios",
        sa.Column("slug", sa.String(255), nullable=True),
    )
    op.create_index("ix_studios_slug", "studios", ["slug"], unique=True)

    # slots: service_id, schedule_id, course_price_cents, status
    op.add_column(
        "slots",
        sa.Column("service_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "slots",
        sa.Column("schedule_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "slots",
        sa.Column("course_price_cents", sa.Integer(), nullable=True),
    )
    op.add_column(
        "slots",
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
    )
    op.create_foreign_key(
        "slots_service_id_fkey",
        "slots",
        "services",
        ["service_id"],
        ["id"],
    )
    op.create_foreign_key(
        "slots_schedule_id_fkey",
        "slots",
        "schedules",
        ["schedule_id"],
        ["id"],
    )
    op.create_index("ix_slots_service_id", "slots", ["service_id"])
    op.create_index("ix_slots_schedule_id", "slots", ["schedule_id"])
    op.create_index("ix_slots_status", "slots", ["status"])

    # bookings: booking_type, service_id, order_id, unit_price_cents
    op.add_column(
        "bookings",
        sa.Column(
            "booking_type",
            sa.String(20),
            nullable=False,
            server_default="single",
        ),
    )
    op.add_column(
        "bookings",
        sa.Column("service_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("order_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("unit_price_cents", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "bookings_service_id_fkey",
        "bookings",
        "services",
        ["service_id"],
        ["id"],
    )
    op.create_foreign_key(
        "bookings_order_id_fkey",
        "bookings",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.create_index("ix_bookings_booking_type", "bookings", ["booking_type"])
    op.create_index("ix_bookings_service_id", "bookings", ["service_id"])
    op.create_index("ix_bookings_order_id", "bookings", ["order_id"])


def downgrade() -> None:
    """Downgrade schema: удалить добавленные объекты."""
    # bookings
    op.drop_index("ix_bookings_order_id", table_name="bookings")
    op.drop_index("ix_bookings_service_id", table_name="bookings")
    op.drop_index("ix_bookings_booking_type", table_name="bookings")
    op.drop_constraint("bookings_order_id_fkey", "bookings", type_="foreignkey")
    op.drop_constraint("bookings_service_id_fkey", "bookings", type_="foreignkey")
    op.drop_column("bookings", "unit_price_cents")
    op.drop_column("bookings", "order_id")
    op.drop_column("bookings", "service_id")
    op.drop_column("bookings", "booking_type")

    # slots
    op.drop_index("ix_slots_status", table_name="slots")
    op.drop_index("ix_slots_schedule_id", table_name="slots")
    op.drop_index("ix_slots_service_id", table_name="slots")
    op.drop_constraint("slots_schedule_id_fkey", "slots", type_="foreignkey")
    op.drop_constraint("slots_service_id_fkey", "slots", type_="foreignkey")
    op.drop_column("slots", "status")
    op.drop_column("slots", "course_price_cents")
    op.drop_column("slots", "schedule_id")
    op.drop_column("slots", "service_id")

    # studios
    op.drop_index("ix_studios_slug", table_name="studios")
    op.drop_column("studios", "slug")

    # orders, schedules, services
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_user_id", table_name="orders")
    op.drop_index("ix_orders_service_id", table_name="orders")
    op.drop_index("ix_orders_studio_id", table_name="orders")
    op.drop_table("orders")

    op.drop_index("ix_schedules_service_id", table_name="schedules")
    op.drop_table("schedules")

    op.drop_index("ix_services_type", table_name="services")
    op.drop_index("ix_services_studio_id", table_name="services")
    op.drop_table("services")
