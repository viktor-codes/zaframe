"""UnitOfWork factory and transaction scope — wires module repositories."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.core.uow import UnitOfWork
from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository
from app.modules.booking.order.repository import OrderRepository
from app.modules.booking.repository import BookingRepository
from app.modules.catalog.occurrence.repository import OccurrenceRepository
from app.modules.catalog.schedule.repository import ScheduleTemplateRepository
from app.modules.catalog.service.repository import ServiceRepository
from app.modules.catalog.studio.repository import StudioMemberRepository, StudioRepository
from app.modules.identity.repository import UserRepository
from app.modules.payment.repository import PaymentRepository, ProcessedWebhookEventRepository
from app.modules.search.repository import SearchRepository


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
        studio_members=StudioMemberRepository(session),
        schedule_templates=ScheduleTemplateRepository(session),
        refresh_tokens=RefreshTokenRepository(session),
        orders=OrderRepository(session),
        payments=PaymentRepository(session),
        webhook_events=ProcessedWebhookEventRepository(session),
        search=SearchRepository(session),
    )


@asynccontextmanager
async def _borrow_session(session: AsyncSession | None) -> AsyncGenerator[AsyncSession]:
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
) -> AsyncGenerator[UnitOfWork]:
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
            if auto_commit and not uow.is_committed:
                await uow.commit()
        except Exception:
            if not uow.is_committed:
                await uow.rollback()
            raise
        finally:
            if not auto_commit and not uow.is_committed:
                await uow.rollback()


async def get_uow() -> AsyncGenerator[UnitOfWork]:
    """FastAPI dependency: one UnitOfWork per request with auto-commit."""
    async with uow_scope() as uow:
        yield uow
