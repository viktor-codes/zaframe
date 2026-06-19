"""Unit of Work type — repository wiring lives in uow_factory (import-linter boundary)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository
    from app.modules.booking.order.repository import OrderRepository
    from app.modules.booking.repository import BookingRepository
    from app.modules.catalog.occurrence.repository import OccurrenceRepository
    from app.modules.catalog.schedule.repository import ScheduleTemplateRepository
    from app.modules.catalog.service.repository import ServiceRepository
    from app.modules.catalog.studio.repository import StudioMemberRepository, StudioRepository
    from app.modules.identity.repository import UserRepository
    from app.modules.payment.repository import ProcessedWebhookEventRepository
    from app.modules.search.repository import SearchRepository


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
    studio_members: StudioMemberRepository
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

    @property
    def is_committed(self) -> bool:
        """Whether commit() was called successfully in this scope."""
        return self._committed
