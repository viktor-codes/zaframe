"""Add catalog product lifecycle contracts.

Revision ID: 014_catalog_product_lifecycle
Revises: 013_gdpr_user_privacy
Create Date: 2026-06-20
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "014_catalog_product_lifecycle"
down_revision: str | Sequence[str] | None = "013_gdpr_user_privacy"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Make service and occurrence lifecycle explicit."""
    op.add_column(
        "services",
        sa.Column("visibility", sa.String(20), nullable=False, server_default="published"),
    )
    op.create_check_constraint(
        "ck_services_visibility",
        "services",
        "visibility IN ('draft', 'published', 'archived')",
    )
    op.create_index("ix_services_visibility", "services", ["visibility"])
    op.execute("UPDATE services SET visibility = 'archived' WHERE is_active = false")

    op.add_column(
        "studios",
        sa.Column("cancel_before_hours", sa.Integer(), nullable=False, server_default="24"),
    )
    op.create_check_constraint(
        "ck_studios_cancel_before_hours_non_negative",
        "studios",
        "cancel_before_hours >= 0",
    )

    op.add_column("occurrences", sa.Column("cancelled_at", TZDT, nullable=True))
    op.add_column("occurrences", sa.Column("cancellation_reason", sa.String(500), nullable=True))
    op.execute("UPDATE occurrences SET status = 'scheduled' WHERE status = 'active'")

    op.execute(
        """
        WITH legacy_services AS (
            INSERT INTO services (
                studio_id,
                name,
                description,
                type,
                category,
                duration_minutes,
                max_capacity,
                price_single_cents,
                price_course_cents,
                soft_limit_ratio,
                hard_limit_ratio,
                max_overbooked_ratio,
                tags,
                is_active,
                visibility,
                created_at,
                updated_at
            )
            SELECT
                o.studio_id,
                'Legacy Occurrence Service',
                'Backfilled for occurrences created before service_id became required.',
                'single',
                'yoga',
                GREATEST(
                    1,
                    COALESCE(
                        ROUND(EXTRACT(EPOCH FROM (MIN(o.end_time) - MIN(o.start_time))) / 60)::int,
                        60
                    )
                ),
                GREATEST(1, COALESCE(MAX(o.max_capacity), 1)),
                GREATEST(0, COALESCE(MIN(o.price_cents), 0)),
                NULL,
                1.0,
                1.5,
                0.3,
                '[]'::json,
                true,
                'archived',
                NOW(),
                NOW()
            FROM occurrences o
            WHERE o.service_id IS NULL
            GROUP BY o.studio_id
            RETURNING id, studio_id
        )
        UPDATE occurrences o
        SET service_id = legacy_services.id
        FROM legacy_services
        WHERE o.service_id IS NULL
          AND legacy_services.studio_id = o.studio_id
        """
    )
    op.alter_column("occurrences", "service_id", existing_type=sa.Integer(), nullable=False)
    op.create_check_constraint(
        "ck_occurrences_status",
        "occurrences",
        "status IN ('scheduled', 'cancelled', 'completed')",
    )


def downgrade() -> None:
    """Revert catalog product lifecycle fields."""
    op.execute("ALTER TABLE occurrences DROP CONSTRAINT IF EXISTS ck_occurrences_status")
    op.alter_column("occurrences", "service_id", existing_type=sa.Integer(), nullable=True)
    op.execute("UPDATE occurrences SET status = 'active' WHERE status = 'scheduled'")
    op.drop_column("occurrences", "cancellation_reason")
    op.drop_column("occurrences", "cancelled_at")

    op.execute(
        "ALTER TABLE studios DROP CONSTRAINT IF EXISTS "
        "ck_studios_cancel_before_hours_non_negative"
    )
    op.drop_column("studios", "cancel_before_hours")

    op.drop_index("ix_services_visibility", table_name="services")
    op.execute("ALTER TABLE services DROP CONSTRAINT IF EXISTS ck_services_visibility")
    op.drop_column("services", "visibility")
