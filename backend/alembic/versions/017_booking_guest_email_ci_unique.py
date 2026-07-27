"""Case-insensitive unique index on active booking guest emails.

Revision ID: 017_booking_guest_email_ci_unique
Revises: 016_anonymize_deleted_user_pii
Create Date: 2026-07-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "017_booking_guest_email_ci_unique"
down_revision: str | Sequence[str] | None = "016_anonymize_deleted_user_pii"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ACTIVE_WHERE = "status IN ('pending', 'confirmed') AND guest_email IS NOT NULL"


def upgrade() -> None:
    """Deduplicate case-variants, lowercase emails, recreate unique index on lower()."""
    # Keep the oldest active row; cancel case-variant duplicates before unique index.
    op.execute(
        sa.text(
            f"""
            WITH ranked AS (
                SELECT
                    id,
                    ROW_NUMBER() OVER (
                        PARTITION BY occurrence_id, lower(guest_email)
                        ORDER BY id ASC
                    ) AS rn
                FROM bookings
                WHERE {_ACTIVE_WHERE}
            )
            UPDATE bookings AS b
            SET
                status = 'cancelled',
                cancelled_at = NOW() AT TIME ZONE,
                updated_at = NOW() AT TIME ZONE
            FROM ranked AS r
            WHERE b.id = r.id AND r.rn > 1
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE bookings
            SET guest_email = lower(guest_email)
            WHERE guest_email IS NOT NULL
              AND guest_email <> lower(guest_email)
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE orders
            SET guest_email = lower(guest_email)
            WHERE guest_email IS NOT NULL
              AND guest_email <> lower(guest_email)
            """
        )
    )

    op.drop_index(
        "uq_bookings_occurrence_guest_email_active",
        table_name="bookings",
    )
    op.execute(
        sa.text(
            f"""
            CREATE UNIQUE INDEX uq_bookings_occurrence_guest_email_active
            ON bookings (occurrence_id, lower(guest_email))
            WHERE {_ACTIVE_WHERE}
            """
        )
    )


def downgrade() -> None:
    """Restore case-sensitive unique index (data stays lowercased)."""
    op.execute(sa.text("DROP INDEX IF EXISTS uq_bookings_occurrence_guest_email_active"))
    op.create_index(
        "uq_bookings_occurrence_guest_email_active",
        "bookings",
        ["occurrence_id", "guest_email"],
        unique=True,
        postgresql_where=sa.text(_ACTIVE_WHERE),
    )
