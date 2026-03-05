"""use timestamptz and add refresh_tokens

Revision ID: d1a2b3c4d5e6
Revises: c4e8b2a1903f
Create Date: 2026-03-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "c4e8b2a1903f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Переводим даты/время в TIMESTAMPTZ и добавляем таблицу refresh_tokens."""
    # 1) Конвертация существующих timestamp-колонок в timestamptz (UTC)
    timestamp_columns: dict[str, list[str]] = {
        "users": [
            "magic_link_expires_at",
            "created_at",
            "updated_at",
            "last_login_at",
        ],
        "guest_sessions": [
            "expires_at",
            "created_at",
            "updated_at",
        ],
        "studios": [
            "created_at",
            "updated_at",
        ],
        "slots": [
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ],
        "bookings": [
            "created_at",
            "updated_at",
            "cancelled_at",
        ],
        "services": [
            "created_at",
            "updated_at",
        ],
        "schedules": [
            "created_at",
            "updated_at",
        ],
        "orders": [
            "created_at",
            "updated_at",
        ],
    }

    for table, columns in timestamp_columns.items():
        for column in columns:
            op.execute(
                f"ALTER TABLE {table} "
                f"ALTER COLUMN {column} "
                f"TYPE timestamptz USING {column} AT TIME ZONE 'UTC'"
            )

    # 2) Таблица для управления refresh-токенами (сессиями)
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_refresh_tokens_user_id",
        "refresh_tokens",
        ["user_id"],
    )
    op.create_index(
        "ix_refresh_tokens_jti",
        "refresh_tokens",
        ["jti"],
        unique=True,
    )
    op.create_index(
        "ix_refresh_tokens_expires_at",
        "refresh_tokens",
        ["expires_at"],
    )
    op.create_index(
        "ix_refresh_tokens_revoked_at",
        "refresh_tokens",
        ["revoked_at"],
    )


def downgrade() -> None:
    """Откат: удаляем refresh_tokens и возвращаем timestamp без TZ."""
    # 1) Удаляем таблицу refresh_tokens
    op.drop_index("ix_refresh_tokens_revoked_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")

    # 2) Конвертируем timestamptz обратно в timestamp without time zone
    timestamp_columns: dict[str, list[str]] = {
        "users": [
            "magic_link_expires_at",
            "created_at",
            "updated_at",
            "last_login_at",
        ],
        "guest_sessions": [
            "expires_at",
            "created_at",
            "updated_at",
        ],
        "studios": [
            "created_at",
            "updated_at",
        ],
        "slots": [
            "start_time",
            "end_time",
            "created_at",
            "updated_at",
        ],
        "bookings": [
            "created_at",
            "updated_at",
            "cancelled_at",
        ],
        "services": [
            "created_at",
            "updated_at",
        ],
        "schedules": [
            "created_at",
            "updated_at",
        ],
        "orders": [
            "created_at",
            "updated_at",
        ],
    }

    for table, columns in timestamp_columns.items():
        for column in columns:
            op.execute(
                f"ALTER TABLE {table} "
                f"ALTER COLUMN {column} "
                f"TYPE timestamp WITHOUT TIME ZONE "
                f"USING {column} AT TIME ZONE 'UTC'"
            )

