"""Rename Slot/Schedule tables and columns per ADR-002 domain vocabulary.

Revision ID: 005_domain_vocabulary
Revises: 004_processed_webhook_events
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_domain_vocabulary"
down_revision: Union[str, Sequence[str], None] = "004_processed_webhook_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ACTIVE_WHERE = "status IN ('pending', 'confirmed')"


def upgrade() -> None:
    """slots→occurrences, schedules→schedule_templates, bookings.slot_id→occurrence_id."""
    op.drop_index("uq_bookings_slot_guest_email_active", table_name="bookings")
    op.drop_index("uq_bookings_slot_user_id_active", table_name="bookings")

    op.rename_table("schedules", "schedule_templates")
    op.execute("ALTER INDEX ix_schedules_id RENAME TO ix_schedule_templates_id")
    op.execute("ALTER INDEX ix_schedules_service_id RENAME TO ix_schedule_templates_service_id")

    op.rename_table("slots", "occurrences")
    op.execute("ALTER INDEX ix_slots_id RENAME TO ix_occurrences_id")
    op.execute("ALTER INDEX ix_slots_studio_id RENAME TO ix_occurrences_studio_id")
    op.execute("ALTER INDEX ix_slots_service_id RENAME TO ix_occurrences_service_id")
    op.execute("ALTER INDEX ix_slots_schedule_id RENAME TO ix_occurrences_schedule_template_id")
    op.execute("ALTER INDEX ix_slots_start_time RENAME TO ix_occurrences_start_time")
    op.execute("ALTER INDEX ix_slots_status RENAME TO ix_occurrences_status")
    op.execute(
        "ALTER INDEX idx_slots_studio_service_start_time "
        "RENAME TO idx_occurrences_studio_service_start_time"
    )

    op.alter_column(
        "occurrences",
        "schedule_id",
        new_column_name="schedule_template_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.alter_column(
        "bookings",
        "slot_id",
        new_column_name="occurrence_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.execute("ALTER INDEX ix_bookings_slot_id RENAME TO ix_bookings_occurrence_id")

    op.create_index(
        "uq_bookings_occurrence_guest_email_active",
        "bookings",
        ["occurrence_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND guest_email IS NOT NULL"),
    )
    op.create_index(
        "uq_bookings_occurrence_user_id_active",
        "bookings",
        ["occurrence_id", "user_id"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND user_id IS NOT NULL"),
    )

    op.execute("UPDATE services SET type = 'single' WHERE type = 'single_class'")


def downgrade() -> None:
    """Reverse ADR-002 table/column renames (destructive if single_class rows exist)."""
    op.execute("UPDATE services SET type = 'single_class' WHERE type = 'single'")

    op.drop_index("uq_bookings_occurrence_user_id_active", table_name="bookings")
    op.drop_index("uq_bookings_occurrence_guest_email_active", table_name="bookings")

    op.alter_column(
        "bookings",
        "occurrence_id",
        new_column_name="slot_id",
        existing_type=sa.Integer(),
        existing_nullable=False,
    )
    op.execute("ALTER INDEX ix_bookings_occurrence_id RENAME TO ix_bookings_slot_id")

    op.alter_column(
        "occurrences",
        "schedule_template_id",
        new_column_name="schedule_id",
        existing_type=sa.Integer(),
        existing_nullable=True,
    )

    op.execute(
        "ALTER INDEX idx_occurrences_studio_service_start_time "
        "RENAME TO idx_slots_studio_service_start_time"
    )
    op.execute("ALTER INDEX ix_occurrences_status RENAME TO ix_slots_status")
    op.execute("ALTER INDEX ix_occurrences_start_time RENAME TO ix_slots_start_time")
    op.execute("ALTER INDEX ix_occurrences_schedule_template_id RENAME TO ix_slots_schedule_id")
    op.execute("ALTER INDEX ix_occurrences_service_id RENAME TO ix_slots_service_id")
    op.execute("ALTER INDEX ix_occurrences_studio_id RENAME TO ix_slots_studio_id")
    op.execute("ALTER INDEX ix_occurrences_id RENAME TO ix_slots_id")

    op.rename_table("occurrences", "slots")
    op.execute("ALTER INDEX ix_schedule_templates_service_id RENAME TO ix_schedules_service_id")
    op.execute("ALTER INDEX ix_schedule_templates_id RENAME TO ix_schedules_id")
    op.rename_table("schedule_templates", "schedules")

    op.create_index(
        "uq_bookings_slot_guest_email_active",
        "bookings",
        ["slot_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND guest_email IS NOT NULL"),
    )
    op.create_index(
        "uq_bookings_slot_user_id_active",
        "bookings",
        ["slot_id", "user_id"],
        unique=True,
        postgresql_where=sa.text(f"{_ACTIVE_WHERE} AND user_id IS NOT NULL"),
    )
