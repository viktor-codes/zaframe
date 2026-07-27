"""Repository for booking create idempotency keys."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import WriteRepositoryMixin
from app.models.booking_idempotency_key import BookingIdempotencyKey


class BookingIdempotencyRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, idempotency_key: str) -> BookingIdempotencyKey | None:
        result = await self._session.execute(
            select(BookingIdempotencyKey).where(
                BookingIdempotencyKey.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    async def add_key(
        self,
        *,
        idempotency_key: str,
        request_fingerprint: str,
        resource_kind: str,
        resource_id: int,
        expires_at: datetime,
    ) -> BookingIdempotencyKey:
        row = BookingIdempotencyKey(
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            resource_kind=resource_kind,
            resource_id=resource_id,
            expires_at=expires_at,
        )
        return await self.add(row)
