"""
Webhook endpoints called by external services, not by the frontend.

Stripe webhooks require the raw body for signature verification.
The endpoint must not live under /api/v1 because Stripe calls it directly.

Router responsibility: parse payload, verify signature, and extract data.
Payment confirmation business logic lives in the payment service.
"""

from typing import Any

import stripe
import structlog
from fastapi import APIRouter, Request, Response

from app.core.config import settings
from app.core.middleware.logging_middleware import REQUEST_ID_STATE_KEY
from app.core.uow_factory import uow_scope
from app.modules.payment.stripe_client import run_stripe
from app.modules.payment.webhook_outcome import WebhookOutcome
from app.modules.payment.webhook_processor import process_stripe_webhook_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(request: Request) -> Response:
    """
    Handle Stripe webhook events.

    Verifies the signature, parses checkout.session.completed events, and delegates
    payment confirmation to the webhook processor.

    Returns 503 when processing is incomplete so Stripe retries until durable success.
    """
    logger = structlog.get_logger(__name__)
    request_id = getattr(request.state, REQUEST_ID_STATE_KEY, None)

    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status_code=503, content="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        # WHY: construct_event does sync crypto/IO helpers; keep the event loop free.
        event: Any = await run_stripe(
            lambda: stripe.Webhook.construct_event(  # pyright: ignore[reportUnknownMemberType]
                payload,
                sig_header,
                webhook_secret,
            )
        )
    except ValueError as e:
        logger.warning(
            "webhook_value_error",
            request_id=request_id,
            error_type=type(e).__name__,
        )
        return Response(status_code=400, content="Invalid payload")
    except stripe.SignatureVerificationError as e:
        logger.warning(
            "webhook_signature_verification_error",
            request_id=request_id,
            error_type=type(e).__name__,
        )
        return Response(status_code=400, content="Invalid signature")

    async with uow_scope(auto_commit=False) as uow:
        outcome = await process_stripe_webhook_event(
            uow, event=event, request_id=request_id
        )

    if outcome == WebhookOutcome.RETRY:
        logger.warning(
            "webhook_processing_incomplete",
            request_id=request_id,
            event_id=str(event.id),
            event_type=str(event.type),
            idempotency_outcome="retry",
        )
        return Response(status_code=503, content="Webhook processing incomplete")

    return Response(status_code=200)
