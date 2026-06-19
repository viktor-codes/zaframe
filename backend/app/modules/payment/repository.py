"""Repositories for payment ledger and processed Stripe webhook events."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.repository import WriteRepositoryMixin
from app.models.booking import Booking
from app.models.occurrence import Occurrence
from app.models.order import Order
from app.models.payment import Payment, Refund
from app.models.processed_webhook_event import ProcessedWebhookEvent


class PaymentRepository(WriteRepositoryMixin):
    """Repository for local payment/refund ledger rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, payment_id: int) -> Payment | None:
        """Fetch one payment with linked booking/order context."""
        result = await self._session.execute(
            select(Payment)
            .options(
                selectinload(Payment.order),
                selectinload(Payment.booking).selectinload(Booking.occurrence),
            )
            .where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_update(self, payment_id: int) -> Payment | None:
        """Fetch one payment for refund mutation under a row lock."""
        result = await self._session.execute(
            select(Payment)
            .options(
                selectinload(Payment.order),
                selectinload(Payment.booking).selectinload(Booking.occurrence),
            )
            .where(Payment.id == payment_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_by_checkout_session_id(self, checkout_session_id: str) -> Payment | None:
        """Fetch a payment by Stripe Checkout Session id."""
        result = await self._session.execute(
            select(Payment).where(Payment.stripe_checkout_session_id == checkout_session_id)
        )
        return result.scalar_one_or_none()

    async def list_for_studio(
        self,
        *,
        studio_id: int,
        status: str | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        booking_id: int | None = None,
        order_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Payment]:
        """List payments belonging to a studio via order or booking occurrence."""
        stmt = (
            select(Payment)
            .outerjoin(Order, Order.id == Payment.order_id)
            .outerjoin(Booking, Booking.id == Payment.booking_id)
            .outerjoin(Occurrence, Occurrence.id == Booking.occurrence_id)
            .options(
                selectinload(Payment.order),
                selectinload(Payment.booking).selectinload(Booking.occurrence),
            )
            .where(or_(Order.studio_id == studio_id, Occurrence.studio_id == studio_id))
        )
        if status is not None:
            stmt = stmt.where(Payment.status == status)
        if start_at is not None:
            stmt = stmt.where(Payment.created_at >= start_at)
        if end_at is not None:
            stmt = stmt.where(Payment.created_at <= end_at)
        if booking_id is not None:
            stmt = stmt.where(Payment.booking_id == booking_id)
        if order_id is not None:
            stmt = stmt.where(Payment.order_id == order_id)
        stmt = stmt.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def add_refund(self, refund: Refund) -> Refund:
        """Persist a refund row."""
        return await self.add(refund)

    async def get_refund_by_stripe_refund_id(self, stripe_refund_id: str) -> Refund | None:
        """Fetch refund with payment context by Stripe refund id."""
        result = await self._session.execute(
            select(Refund)
            .options(
                selectinload(Refund.payment).selectinload(Payment.order),
                selectinload(Refund.payment)
                .selectinload(Payment.booking)
                .selectinload(Booking.occurrence),
            )
            .where(Refund.stripe_refund_id == stripe_refund_id)
        )
        return result.scalar_one_or_none()

    async def get_refund_by_idempotency_key(self, idempotency_key: str) -> Refund | None:
        """Fetch refund with payment context by API idempotency key."""
        result = await self._session.execute(
            select(Refund)
            .options(
                selectinload(Refund.payment).selectinload(Payment.order),
                selectinload(Refund.payment)
                .selectinload(Payment.booking)
                .selectinload(Booking.occurrence),
            )
            .where(Refund.idempotency_key == idempotency_key)
        )
        return result.scalar_one_or_none()


class ProcessedWebhookEventRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def exists_by_event_id(self, event_id: str) -> bool:
        """True when this Stripe event.id was already processed successfully."""
        result = await self._session.execute(
            select(ProcessedWebhookEvent.id)
            .where(ProcessedWebhookEvent.event_id == event_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def record(self, *, event_id: str, event_type: str) -> ProcessedWebhookEvent:
        """Persist a successfully processed webhook event."""
        return await self.add(
            ProcessedWebhookEvent(
                event_id=event_id,
                event_type=event_type,
            )
        )
