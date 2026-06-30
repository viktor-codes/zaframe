"""Repository for the User entity."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import WriteRepositoryMixin
from app.models.user import User


class UserRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.id == user_id,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.email == email,
                User.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, user_id: int) -> User | None:
        """Explicit support/admin lookup that can return soft-deleted users."""
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email_including_deleted(self, email: str) -> User | None:
        """Explicit support/admin lookup that can return soft-deleted users."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
