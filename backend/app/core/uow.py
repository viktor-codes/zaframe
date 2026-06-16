"""Unit of Work type — repository wiring lives in uow_factory (import-linter boundary)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class UnitOfWork:
    """
    Unit of Work for a single use-case within one DB transaction.

    Services use uow.bookings, uow.users, etc. for reads/writes.
    Transaction boundaries are managed by uow_scope() — not by callers.
    """

    session: AsyncSession
    bookings: Any
    otp_codes: Any
    users: Any
    studios: Any
    occurrences: Any
    services: Any
    schedule_templates: Any
    refresh_tokens: Any
    orders: Any
    webhook_events: Any
    search: Any
    _committed: bool = field(default=False, init=False, repr=False)

    async def commit(self) -> None:
        await self.session.commit()
        self._committed = True

    async def rollback(self) -> None:
        await self.session.rollback()
        self._committed = False
