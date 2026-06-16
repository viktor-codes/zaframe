"""Repository for Booking entities."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import WriteRepositoryMixin
from app.modules.booking.repository.capacity_queries import BookingCapacityQueriesMixin
from app.modules.booking.repository.list_queries import BookingListQueriesMixin


class BookingRepository(
    BookingListQueriesMixin,
    BookingCapacityQueriesMixin,
    WriteRepositoryMixin,
):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
