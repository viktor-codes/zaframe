"""Repository for the Order entity."""

from typing import Any, cast

from sqlalchemy import func, or_, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repository import WriteRepositoryMixin
from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderStatus
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

    async def count_for_user(
        self,
        *,
        user_id: int,
        user_email: str,
    ) -> int:
        normalized_email = user_email.strip().lower()
        result = await self._session.execute(
            select(func.count())
            .select_from(Order)
            .where(
                or_(
                    Order.user_id == user_id,
                    func.lower(Order.guest_email) == normalized_email,
                )
            )
        )
        return result.scalar_one()

    async def count_for_studio_member(
        self,
        *,
        user_id: int,
        studio_id: int | None = None,
    ) -> int:
        query = (
            select(func.count(func.distinct(Order.id)))
            .select_from(Order)
            .join(Studio, Studio.id == Order.studio_id)
            .outerjoin(
                StudioMember,
                (StudioMember.studio_id == Studio.id) & (StudioMember.user_id == user_id),
            )
            .where(or_(Studio.owner_id == user_id, StudioMember.user_id == user_id))
        )
        if studio_id is not None:
            query = query.where(Order.studio_id == studio_id)
        result = await self._session.execute(query)
        return result.scalar_one()

    async def expire_pending_without_active_bookings(
        self,
        *,
        order_ids: list[int],
    ) -> int:
        """Mark pending orders expired once none of their bookings can still become paid."""
        if not order_ids:
            return 0

        active_booking_exists = (
            select(Booking.id)
            .where(
                Booking.order_id == Order.id,
                Booking.status.in_(
                    (
                        BookingStatus.PENDING,
                        BookingStatus.CONFIRMED,
                    )
                ),
            )
            .exists()
        )
        result = await self._session.execute(
            update(Order)
            .where(
                Order.id.in_(order_ids),
                Order.status == OrderStatus.PENDING,
                ~active_booking_exists,
            )
            .values(status=OrderStatus.EXPIRED, access_token=None)
        )
        await self._session.flush()
        cursor = cast(CursorResult[Any], result)
        return cursor.rowcount or 0

    async def attach_guest_orders_by_email(
        self,
        *,
        user_id: int,
        guest_email: str,
    ) -> int:
        """Attach guest orders to a verified account by normalized guest email."""
        normalized_email = guest_email.strip().lower()
        result = await self._session.execute(
            update(Order)
            .where(
                Order.user_id.is_(None),
                func.lower(Order.guest_email) == normalized_email,
            )
            .values(user_id=user_id)
        )
        await self._session.flush()
        cursor = cast(CursorResult[Any], result)
        return cursor.rowcount or 0
