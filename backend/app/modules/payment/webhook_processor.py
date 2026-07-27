"""Stripe webhook processing use-cases."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy.exc import IntegrityError

from app.core.uow import UnitOfWork
from app.modules.payment.webhook_handlers import (
    process_account_updated,
    process_refund_updated,
)
from app.modules.payment.webhook_outcome import WebhookOutcome
from app.modules.payment.webhook_paid_checkout import process_paid_checkout

# Re-export parsers for tests that import from webhook_processor.
from app.modules.payment.webhook_parsing import (
    parse_checkout_session_metadata,
    parse_payment_intent_id,
)

__all__ = [
    "process_stripe_webhook_event",
    "parse_checkout_session_metadata",
    "parse_payment_intent_id",
    "WebhookOutcome",
]

_CHECKOUT_SUCCESS_EVENTS = frozenset(
    {"checkout.session.completed", "checkout.session.async_payment_succeeded"}
)
_CHECKOUT_FAILED_EVENTS = frozenset({"checkout.session.async_payment_failed"})
_SUPPORTED_EVENTS = (
    _CHECKOUT_SUCCESS_EVENTS
    | _CHECKOUT_FAILED_EVENTS
    | {
        "account.updated",
        "refund.updated",
    }
)


async def process_stripe_webhook_event(
    uow: UnitOfWork,
    *,
    event: Any,
    request_id: str | None = None,
) -> WebhookOutcome:
    """Process supported Stripe webhook events idempotently."""
    logger = structlog.get_logger(__name__)
    event_id = str(event.id)
    event_type = str(event.type)
    if event_type not in _SUPPORTED_EVENTS:
        return WebhookOutcome.PROCESSED

    try:
        if await uow.webhook_events.exists_by_event_id(event_id):
            logger.info(
                "webhook_duplicate_event_skipped",
                request_id=request_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="duplicate",
            )
            return WebhookOutcome.DUPLICATE

        if event_type == "account.updated":
            return await process_account_updated(
                uow,
                account=event.data.object,
                event_id=event_id,
                event_type=event_type,
                request_id=request_id,
            )

        if event_type == "refund.updated":
            return await process_refund_updated(
                uow,
                stripe_refund=event.data.object,
                event_id=event_id,
                event_type=event_type,
                request_id=request_id,
            )

        return await process_paid_checkout(
            uow,
            session=event.data.object,
            event_id=event_id,
            event_type=event_type,
            request_id=request_id,
        )
    except IntegrityError:
        await uow.rollback()
        logger.info(
            "webhook_duplicate_event_race",
            request_id=request_id,
            event_id=event_id,
            event_type=event_type,
            idempotency_outcome="duplicate_race",
        )
        return WebhookOutcome.DUPLICATE
    except Exception:
        await uow.rollback()
        raise
