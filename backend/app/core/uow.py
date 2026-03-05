from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class UnitOfWork:
    """
    Unit of Work для работы с БД в рамках одного use-case.

    На первом этапе это тонкая обёртка над AsyncSession.
    Позже здесь можно разместить репозитории и дополнительную инфраструктуру.
    """

    session: AsyncSession

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

