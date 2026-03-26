"""
Репозиторий для сущности Order.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_id_with_service(self, order_id: int) -> Order | None:
        result = await self._session.execute(
            select(Order).options(selectinload(Order.service)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
