"""Repository for processed Stripe webhook events (idempotency ledger)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import WriteRepositoryMixin
from app.models.processed_webhook_event import ProcessedWebhookEvent


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
