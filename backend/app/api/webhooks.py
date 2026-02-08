"""
Webhook endpoints (вызываются внешними сервисами, не фронтендом).

Stripe webhook требует raw body для проверки подписи.
Эндпоинт не должен быть под /api/v1 — Stripe вызывает его напрямую.
"""
import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import stripe

from app.core.config import settings
from app.core.database import async_session_maker
from app.models.booking import Booking, BookingStatus

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _get_stripe_client() -> stripe.StripeClient:
    """Получить Stripe-клиент."""
    if not settings.STRIPE_SECRET_KEY:
        raise ValueError("STRIPE_SECRET_KEY не настроен")
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


@router.post("/stripe", status_code=200)
async def stripe_webhook(request: Request) -> Response:
    """
    Обработчик Stripe webhook.

    Проверяет подпись, обрабатывает checkout.session.completed.
    Идемпотентность: если бронирование уже confirmed — пропускаем.
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        return Response(status_code=500, content="Webhook secret not configured")

    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        logger.warning("Webhook ValueError: %s", e)
        return Response(status_code=400, content="Invalid payload")
    except stripe.SignatureVerificationError as e:
        logger.warning("Webhook SignatureVerificationError: %s", e)
        return Response(status_code=400, content="Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        metadata = getattr(session, "metadata", None) or {}
        if isinstance(metadata, dict):
            booking_id_str = metadata.get("booking_id")
        else:
            booking_id_str = getattr(metadata, "booking_id", None)
        if not booking_id_str:
            logger.warning("Webhook checkout.session.completed: missing metadata.booking_id")
            return Response(status_code=200)

        try:
            booking_id = int(booking_id_str)
        except ValueError:
            return Response(status_code=200)

        # payment_intent: может быть строка (id) или объект с .id
        pi = getattr(session, "payment_intent", None)
        if pi is None and isinstance(session, dict):
            pi = session.get("payment_intent")
        payment_intent_id = None
        if pi is not None:
            payment_intent_id = getattr(pi, "id", None) or (str(pi) if isinstance(pi, str) else None)

        async with async_session_maker() as db:
            result = await db.execute(select(Booking).where(Booking.id == booking_id))
            booking = result.scalar_one_or_none()
            if booking is None:
                logger.warning("Webhook: booking_id=%s not found", booking_id)
                return Response(status_code=200)
            if booking.status == BookingStatus.CONFIRMED:
                return Response(status_code=200)  # идемпотентность

            booking.status = BookingStatus.CONFIRMED
            booking.payment_status = "succeeded"
            if payment_intent_id:
                booking.payment_intent_id = payment_intent_id
            await db.commit()
            logger.info("Webhook: booking_id=%s confirmed", booking_id)

    return Response(status_code=200)
