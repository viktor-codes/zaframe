from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, func, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class RefreshToken(Base):
    """
    Сессия refresh-токена для пользователя.

    Позволяет реализовать:
    - ротацию refresh-токенов (одноразовое использование jti)
    - logout со всех устройств (ревокация всех токенов пользователя)
    - аудит активных сессий.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    jti: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens",
    )

    def is_active(self, now: datetime | None = None) -> bool:
        """Активен ли токен на момент now (по умолчанию сейчас)."""
        if now is None:
            now = datetime.now(timezone.utc)
        if self.revoked_at is not None:
            return False
        return self.expires_at > now

