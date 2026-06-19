"""
Репозиторий для сущности Order.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repository import WriteRepositoryMixin
from app.models.booking import Booking
from app.models.order import Order
from app.models.studio import Studio
from app.models.studio_member import StudioMember


class OrderRepository(WriteRepositoryMixin):
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

    async def get_by_id_with_service_and_studio(self, order_id: int) -> Order | None:
        result = await self._session.execute(
            select(Order)
            .options(selectinload(Order.service), selectinload(Order.studio))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: int,
        user_email: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        normalized_email = user_email.strip().lower()
        result = await self._session.execute(
            select(Order)
            .options(
                selectinload(Order.service),
                selectinload(Order.bookings).load_only(
                    Booking.id,
                    Booking.occurrence_id,
                    Booking.status,
                    Booking.payment_status,
                ),
            )
            .where(
                or_(
                    Order.user_id == user_id,
                    func.lower(Order.guest_email) == normalized_email,
                )
            )
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def list_for_studio_member(
        self,
        *,
        user_id: int,
        studio_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Order]:
        query = (
            select(Order)
            .join(Studio, Studio.id == Order.studio_id)
            .outerjoin(
                StudioMember,
                (StudioMember.studio_id == Studio.id) & (StudioMember.user_id == user_id),
            )
            .options(
                selectinload(Order.service),
                selectinload(Order.bookings).load_only(
                    Booking.id,
                    Booking.occurrence_id,
                    Booking.status,
                    Booking.payment_status,
                ),
            )
            .where(or_(Studio.owner_id == user_id, StudioMember.user_id == user_id))
            .distinct()
        )
        if studio_id is not None:
            query = query.where(Order.studio_id == studio_id)
        query = query.order_by(Order.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(query)
        return list(result.scalars().all())
