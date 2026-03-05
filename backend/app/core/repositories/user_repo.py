"""
Репозиторий для сущности User.
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_magic_link_token(
        self, token_hash: str, expires_after: datetime
    ) -> User | None:
        result = await self._session.execute(
            select(User).where(
                User.magic_link_token == token_hash,
                User.magic_link_expires_at > expires_after,
            )
        )
        return result.scalar_one_or_none()
