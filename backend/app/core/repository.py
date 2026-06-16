"""Shared write helpers for SQLAlchemy repositories."""

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class WriteRepositoryMixin:
    _session: AsyncSession

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def add_all(self, entities: list[T]) -> list[T]:
        for entity in entities:
            self._session.add(entity)
        await self._session.flush()
        for entity in entities:
            await self._session.refresh(entity)
        return entities

    async def save(self, entity: T) -> T:
        """Persist in-memory changes on a tracked entity."""
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def flush(self) -> None:
        await self._session.flush()

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()
