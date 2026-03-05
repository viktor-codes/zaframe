from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories import (
    BookingRepository,
    OrderRepository,
    RefreshTokenRepository,
    ScheduleRepository,
    ServiceRepository,
    SlotRepository,
    StudioRepository,
    UserRepository,
)


@dataclass
class UnitOfWork:
    """
    Unit of Work для работы с БД в рамках одного use-case.

    Содержит сессию и репозитории; сервисы получают uow и используют
    uow.bookings, uow.users и т.д. для выборок, uow.session для add/delete/flush.
    """

    session: AsyncSession
    bookings: BookingRepository
    users: UserRepository
    studios: StudioRepository
    slots: SlotRepository
    services: ServiceRepository
    schedules: ScheduleRepository
    refresh_tokens: RefreshTokenRepository
    orders: OrderRepository

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def create_uow(session: AsyncSession) -> UnitOfWork:
    """Фабрика UoW: создаёт репозитории с одной и той же сессией."""
    return UnitOfWork(
        session=session,
        bookings=BookingRepository(session),
        users=UserRepository(session),
        studios=StudioRepository(session),
        slots=SlotRepository(session),
        services=ServiceRepository(session),
        schedules=ScheduleRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        orders=OrderRepository(session),
    )

