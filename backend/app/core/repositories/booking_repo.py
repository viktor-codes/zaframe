"""
Репозиторий для сущности Booking.

Все выборки по бронированиям инкапсулированы здесь.
"""
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking, BookingStatus


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking).where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_slot(self, booking_id: int) -> Booking | None:
        result = await self._session.execute(
            select(Booking)
            .options(selectinload(Booking.slot))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def list_(
        self,
        *,
        skip: int = 0,
        limit: int = 20,
        slot_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
    ) -> list[Booking]:
        query = select(Booking)
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        if guest_email is not None:
            query = query.where(Booking.guest_email == guest_email)
        if status is not None:
            query = query.where(Booking.status == status)
        query = query.offset(skip).limit(limit).order_by(Booking.created_at.desc())
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        *,
        slot_id: int | None = None,
        user_id: int | None = None,
        guest_email: str | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Booking)
        if slot_id is not None:
            query = query.where(Booking.slot_id == slot_id)
        if user_id is not None:
            query = query.where(Booking.user_id == user_id)
        if guest_email is not None:
            query = query.where(Booking.guest_email == guest_email)
        if status is not None:
            query = query.where(Booking.status == status)
        result = await self._session.execute(query)
        return result.scalar_one_or_none() or 0

    async def count_confirmed_by_slot(self, slot_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.CONFIRMED,
            )
        )
        return result.scalar_one_or_none() or 0

    async def count_pending_by_slot(self, slot_id: int) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Booking)
            .where(
                Booking.slot_id == slot_id,
                Booking.status == BookingStatus.PENDING,
            )
        )
        return result.scalar_one_or_none() or 0

    async def get_confirmed_pending_counts_by_slot_ids(
        self, slot_ids: list[int]
    ) -> dict[int, tuple[int, int]]:
        """Для каждого slot_id возвращает (confirmed_count, pending_count)."""
        if not slot_ids:
            return {}
        counts_q = select(
            Booking.slot_id,
            func.sum(
                case(
                    (Booking.status == BookingStatus.CONFIRMED, 1),
                    else_=0,
                )
            ).label("confirmed"),
            func.sum(
                case(
                    (Booking.status == BookingStatus.PENDING, 1),
                    else_=0,
                )
            ).label("pending"),
        ).where(Booking.slot_id.in_(slot_ids)).group_by(Booking.slot_id)
        result = await self._session.execute(counts_q)
        return {
            row.slot_id: (row.confirmed or 0, row.pending or 0)
            for row in result
        }
