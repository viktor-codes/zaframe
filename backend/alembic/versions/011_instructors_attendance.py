"""Add occurrence instructors and attendance timestamps.

Revision ID: 011_instructors_attendance
Revises: 010_rbac_studio_members
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011_instructors_attendance"
down_revision: str | Sequence[str] | None = "010_rbac_studio_members"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Add instructor assignment and attendance markers."""
    op.add_column(
        "occurrences",
        sa.Column("instructor_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_occurrences_studio_members_instructor_id",
        "occurrences",
        "studio_members",
        ["instructor_id"],
        ["id"],
    )
    op.create_index("ix_occurrences_instructor_id", "occurrences", ["instructor_id"])

    op.add_column("bookings", sa.Column("checked_in_at", TZDT, nullable=True))
    op.add_column("bookings", sa.Column("no_show_at", TZDT, nullable=True))


def downgrade() -> None:
    """Remove instructor assignment and attendance markers."""
    op.drop_column("bookings", "no_show_at")
    op.drop_column("bookings", "checked_in_at")

    op.drop_index("ix_occurrences_instructor_id", table_name="occurrences")
    op.drop_constraint(
        "fk_occurrences_studio_members_instructor_id",
        "occurrences",
        type_="foreignkey",
    )
    op.drop_column("occurrences", "instructor_id")
