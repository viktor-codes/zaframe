"""Rename legacy slot FK and PK constraint names after domain vocabulary migration.

Revision ID: 007_rename_slot_fk_constraints
Revises: 006_booking_access_token
Create Date: 2026-06-15

WHY: op.rename_table in 005 left Postgres auto-generated constraint names unchanged;
clean names keep pg_constraint free of "slot" and Alembic autogenerate quiet.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "007_rename_slot_fk_constraints"
down_revision: Union[str, Sequence[str], None] = "006_booking_access_token"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Names from: SELECT conname FROM pg_constraint WHERE conname LIKE '%slot%';
_BOOKINGS_OCCURRENCE_FK_OLD = "bookings_slot_id_fkey"
_BOOKINGS_OCCURRENCE_FK_NEW = "fk_bookings_occurrences_occurrence_id"

_OCCURRENCES_STUDIO_FK_OLD = "slots_studio_id_fkey"
_OCCURRENCES_STUDIO_FK_NEW = "fk_occurrences_studios_studio_id"

_OCCURRENCES_SERVICE_FK_OLD = "slots_service_id_fkey"
_OCCURRENCES_SERVICE_FK_NEW = "fk_occurrences_services_service_id"

_OCCURRENCES_SCHEDULE_TEMPLATE_FK_OLD = "slots_schedule_id_fkey"
_OCCURRENCES_SCHEDULE_TEMPLATE_FK_NEW = "fk_occurrences_schedule_templates_schedule_template_id"

_OCCURRENCES_PK_OLD = "slots_pkey"
_OCCURRENCES_PK_NEW = "occurrences_pkey"


def upgrade() -> None:
    """Rename slot-era constraint names to domain vocabulary."""
    op.execute(
        f"ALTER TABLE bookings RENAME CONSTRAINT {_BOOKINGS_OCCURRENCE_FK_OLD} "
        f"TO {_BOOKINGS_OCCURRENCE_FK_NEW}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_STUDIO_FK_OLD} "
        f"TO {_OCCURRENCES_STUDIO_FK_NEW}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_SERVICE_FK_OLD} "
        f"TO {_OCCURRENCES_SERVICE_FK_NEW}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_SCHEDULE_TEMPLATE_FK_OLD} "
        f"TO {_OCCURRENCES_SCHEDULE_TEMPLATE_FK_NEW}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_PK_OLD} "
        f"TO {_OCCURRENCES_PK_NEW}"
    )


def downgrade() -> None:
    """Restore legacy slot-era constraint names."""
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_PK_NEW} "
        f"TO {_OCCURRENCES_PK_OLD}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_SCHEDULE_TEMPLATE_FK_NEW} "
        f"TO {_OCCURRENCES_SCHEDULE_TEMPLATE_FK_OLD}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_SERVICE_FK_NEW} "
        f"TO {_OCCURRENCES_SERVICE_FK_OLD}"
    )
    op.execute(
        f"ALTER TABLE occurrences RENAME CONSTRAINT {_OCCURRENCES_STUDIO_FK_NEW} "
        f"TO {_OCCURRENCES_STUDIO_FK_OLD}"
    )
    op.execute(
        f"ALTER TABLE bookings RENAME CONSTRAINT {_BOOKINGS_OCCURRENCE_FK_NEW} "
        f"TO {_BOOKINGS_OCCURRENCE_FK_OLD}"
    )
