from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository
from app.modules.catalog import (
    OccurrenceRepository,
    ScheduleTemplateRepository,
    ServiceRepository,
    StudioRepository,
)
from app.modules.identity import UserRepository
from app.modules.payment import ProcessedWebhookEventRepository
from app.modules.search import SearchRepository
from app.repositories import BookingRepository, OrderRepository


@dataclass
class UnitOfWork:
    """
    Unit of Work for a single use-case within one DB transaction.

    Services use uow.bookings, uow.users, etc. for reads/writes.
    Transaction boundaries are managed by uow_scope() — not by callers.
    """

    session: AsyncSession
    bookings: BookingRepository
    otp_codes: OTPCodeRepository
    users: UserRepository
    studios: StudioRepository
    occurrences: OccurrenceRepository
    services: ServiceRepository
    schedule_templates: ScheduleTemplateRepository
    refresh_tokens: RefreshTokenRepository
    orders: OrderRepository
    webhook_events: ProcessedWebhookEventRepository
    search: SearchRepository
    _committed: bool = field(default=False, init=False, repr=False)

    async def commit(self) -> None:
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self.session.rollback()
        self._committed = False


def create_uow(session: AsyncSession) -> UnitOfWork:
    """Factory: build repositories sharing one AsyncSession."""
    return UnitOfWork(
        session=session,
        bookings=BookingRepository(session),
        otp_codes=OTPCodeRepository(session),
        users=UserRepository(session),
        studios=StudioRepository(session),
        occurrences=OccurrenceRepository(session),
        services=ServiceRepository(session),
        schedule_templates=ScheduleTemplateRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        orders=OrderRepository(session),
        webhook_events=ProcessedWebhookEventRepository(session),
        search=SearchRepository(session),
    )


@asynccontextmanager
async def _borrow_session(session: AsyncSession | None) -> AsyncIterator[AsyncSession]:
    """Yield caller-owned session or open a scoped session from the pool."""
    if session is not None:
        yield session
        return
    async with async_session_maker() as owned_session:
        yield owned_session


@asynccontextmanager
async def uow_scope(
    *,
    session: AsyncSession | None = None,
    auto_commit: bool = True,
) -> AsyncIterator[UnitOfWork]:
    """
    Manage UnitOfWork lifecycle: commit on success, rollback on error.

    Args:
        session: Reuse an existing session (tests, integration fixtures).
        auto_commit: When True, commit after the block unless commit() was already called.
            When False, caller must commit() explicitly; uncommitted work is rolled back on exit.
    """
    async with _borrow_session(session) as active_session:
        uow = create_uow(active_session)
        try:
            yield uow
            if auto_commit and not uow._committed:
                await uow.commit()
        except Exception:
            if not uow._committed:
                await uow.rollback()
            raise
        finally:
            if not auto_commit and not uow._committed:
                await uow.rollback()
