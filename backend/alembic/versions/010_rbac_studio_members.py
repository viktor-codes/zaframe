"""Add global user roles and studio members.

Revision ID: 010_rbac_studio_members
Revises: 009_studio_media_urls
Create Date: 2026-06-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_rbac_studio_members"
down_revision: str | Sequence[str] | None = "009_studio_media_urls"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

user_role_enum = postgresql.ENUM(
    "user",
    "studio_owner",
    "admin",
    name="user_role",
    create_type=False,
)
studio_member_role_enum = postgresql.ENUM(
    "owner",
    "manager",
    "instructor",
    name="studio_member_role",
    create_type=False,
)
TZDT = sa.DateTime(timezone=True)


def upgrade() -> None:
    """Create RBAC schema and backfill owner memberships."""
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    studio_member_role_enum.create(bind, checkfirst=True)

    op.add_column(
        "users",
        sa.Column("role", user_role_enum, nullable=False, server_default="user"),
    )

    op.create_table(
        "studio_members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("studio_id", sa.Integer(), sa.ForeignKey("studios.id"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("role", studio_member_role_enum, nullable=False),
        sa.Column("created_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TZDT, server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("studio_id", "user_id", name="uq_studio_members_studio_user"),
    )
    op.create_index("ix_studio_members_id", "studio_members", ["id"])
    op.create_index("idx_studio_members_studio_id", "studio_members", ["studio_id"])
    op.create_index("idx_studio_members_user_id", "studio_members", ["user_id"])
    op.create_index("ix_studio_members_created_at", "studio_members", ["created_at"])

    op.execute(
        """
        INSERT INTO studio_members (studio_id, user_id, role, created_at, updated_at)
        SELECT id, owner_id, 'owner', NOW(), NOW()
        FROM studios
        ON CONFLICT (studio_id, user_id) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE users
        SET role = 'studio_owner'
        WHERE id IN (SELECT owner_id FROM studios)
        """
    )


def downgrade() -> None:
    """Remove studio membership RBAC schema."""
    bind = op.get_bind()
    op.drop_index("ix_studio_members_created_at", table_name="studio_members")
    op.drop_index("idx_studio_members_user_id", table_name="studio_members")
    op.drop_index("idx_studio_members_studio_id", table_name="studio_members")
    op.drop_index("ix_studio_members_id", table_name="studio_members")
    op.drop_table("studio_members")
    op.drop_column("users", "role")
    studio_member_role_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
