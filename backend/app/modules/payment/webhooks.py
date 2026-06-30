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
from app.modules.payment.webhook_processor import process_stripe_webhook_event

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe", status_code=200)
async def stripe_webhook(request: Request) -> Response:
    """
    Handle Stripe webhook events.

    Verifies the signature, parses checkout.session.completed events, and delegates
    payment confirmation to the webhook processor.
    """
    logger = structlog.get_logger(__name__)
    request_id = getattr(request.state, REQUEST_ID_STATE_KEY, None)

    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status_code=503, content="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event: Any = stripe.Webhook.construct_event(  # pyright: ignore[reportUnknownMemberType]  # WHY: stripe SDK has no type stubs
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
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
        await process_stripe_webhook_event(uow, event=event, request_id=request_id)

    return Response(status_code=200)
