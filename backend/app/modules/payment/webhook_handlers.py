"""Stripe webhook event handlers."""

from __future__ import annotations

import structlog

from app.core.uow import UnitOfWork
from app.modules.payment.service import (
    update_refund_from_stripe_object,
    update_studio_connect_status_from_account,
)
from app.modules.payment.webhook_outcome import WebhookOutcome


async def record_processed_event(uow: UnitOfWork, *, event_id: str, event_type: str) -> None:
    await uow.webhook_events.record(event_id=event_id, event_type=event_type)
    await uow.commit()


async def process_account_updated(
    uow: UnitOfWork,
    *,
    account: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> WebhookOutcome:
    logger = structlog.get_logger(__name__)
    ok = await update_studio_connect_status_from_account(uow, account=account)
    if ok:
        await record_processed_event(uow, event_id=event_id, event_type=event_type)
        logger.info(
            "webhook_stripe_account_updated",
            request_id=request_id,
            event_id=event_id,
            event_type=event_type,
            idempotency_outcome="processed",
        )
        return WebhookOutcome.PROCESSED
    logger.warning(
        "webhook_stripe_account_updated_unmatched",
        request_id=request_id,
        event_id=event_id,
        event_type=event_type,
        idempotency_outcome="unmatched",
    )
    # WHY: poison / unmatched Connect account — ACK so Stripe stops retrying forever.
    await record_processed_event(uow, event_id=event_id, event_type=event_type)
    return WebhookOutcome.PROCESSED


async def process_refund_updated(
    uow: UnitOfWork,
    *,
    stripe_refund: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> WebhookOutcome:
    logger = structlog.get_logger(__name__)
    ok = await update_refund_from_stripe_object(uow, stripe_refund=stripe_refund)
    if ok:
        await record_processed_event(uow, event_id=event_id, event_type=event_type)
        logger.info(
            "webhook_refund_updated",
            request_id=request_id,
            event_id=event_id,
            event_type=event_type,
            idempotency_outcome="processed",
        )
        return WebhookOutcome.PROCESSED
    logger.warning(
        "webhook_refund_updated_unmatched",
        request_id=request_id,
        event_id=event_id,
        event_type=event_type,
        idempotency_outcome="unmatched",
    )
    # WHY: poison / unmatched refund — ACK so Stripe stops retrying forever.
    await record_processed_event(uow, event_id=event_id, event_type=event_type)
    return WebhookOutcome.PROCESSED
