"""add_search_fields_to_studio_and_service

Revision ID: ba2c1fa16678
Revises: 3e50488bde0d
Create Date: 2026-02-13 12:33:50.352395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "ba2c1fa16678"
down_revision: Union[str, Sequence[str], None] = "3e50488bde0d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


service_category_enum = sa.Enum(
    "yoga",
    "boxing",
    "dance",
    "hiit",
    "pilates",
    "martial_arts",
    "strength",
    name="service_category",
)


def upgrade() -> None:
    """Upgrade schema: поля для поиска в студиях и услугах."""
    bind = op.get_bind()

    # === Enum для категории услуги ===
    service_category_enum.create(bind, checkfirst=True)

    # === Таблица services ===
    op.add_column(
        "services",
        sa.Column(
            "category",
            service_category_enum,
            nullable=False,
            server_default="yoga",
        ),
    )
    op.add_column(
        "services",
        sa.Column(
            "tags",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_index(
        "ix_services_category",
        "services",
        ["category"],
        unique=False,
    )

    # === Таблица studios ===
    op.add_column(
        "studios",
        sa.Column("city", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "studios",
        sa.Column("latitude", sa.Float(), nullable=True),
    )
    op.add_column(
        "studios",
        sa.Column("longitude", sa.Float(), nullable=True),
    )
    op.add_column(
        "studios",
        sa.Column(
            "amenities",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.create_index(
        "ix_studios_city",
        "studios",
        ["city"],
        unique=False,
    )

    # Убираем server_default, чтобы соответствовать декларативным моделям
    op.alter_column("services", "category", server_default=None)
    op.alter_column("services", "tags", server_default=None)
    op.alter_column("studios", "amenities", server_default=None)


def downgrade() -> None:
    """Downgrade schema: откат полей поиска и enum."""
    bind = op.get_bind()

    # === Таблица studios ===
    op.drop_index("ix_studios_city", table_name="studios")
    op.drop_column("studios", "amenities")
    op.drop_column("studios", "longitude")
    op.drop_column("studios", "latitude")
    op.drop_column("studios", "city")

    # === Таблица services ===
    op.drop_index("ix_services_category", table_name="services")
    op.drop_column("services", "tags")
    op.drop_column("services", "category")

    # === Enum ===
    service_category_enum.drop(bind, checkfirst=True)
