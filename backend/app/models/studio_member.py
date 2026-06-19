"""Studio membership model for per-studio RBAC."""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.occurrence import Occurrence
    from app.models.studio import Studio
    from app.models.user import User


class StudioMemberRole(enum.StrEnum):
    """Per-studio role used for studio-scoped permissions."""

    OWNER = "owner"
    MANAGER = "manager"
    INSTRUCTOR = "instructor"


class StudioMember(TimestampMixin, Base):
    """A user's role inside a specific studio."""

    __tablename__ = "studio_members"
    __table_args__ = (
        UniqueConstraint("studio_id", "user_id", name="uq_studio_members_studio_user"),
        Index("idx_studio_members_studio_id", "studio_id"),
        Index("idx_studio_members_user_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    studio_id: Mapped[int] = mapped_column(ForeignKey("studios.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(
            "owner",
            "manager",
            "instructor",
            name="studio_member_role",
            create_constraint=False,
        ),
        nullable=False,
    )

    studio: Mapped[Studio] = relationship("Studio", back_populates="members")
    user: Mapped[User] = relationship("User", back_populates="studio_memberships")
    assigned_occurrences: Mapped[list[Occurrence]] = relationship(
        "Occurrence",
        back_populates="instructor",
    )
