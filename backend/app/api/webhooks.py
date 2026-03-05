"""
Webhook endpoints (вызываются внешними сервисами, не фронтендом).

Stripe webhook требует raw body для проверки подписи.
Эндпоинт не должен быть под /api/v1 — Stripe вызывает его напрямую.

Роль роутера: парсинг payload, проверка подписи, извлечение данных.
Бизнес-логика подтверждения оплаты — в сервисе payment.
"""
import logging

from fastapi import APIRouter, Request, Response

import stripe

from app.core.config import settings
from app.core.database import async_session_maker
from app.core.uow import create_uow
from app.services.payment import confirm_booking_after_payment, confirm_order_after_payment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _parse_checkout_session_metadata(session: object) -> tuple[str | None, str | None]:
    """Извлекает booking_id и order_id из metadata Stripe session."""
    metadata = getattr(session, "metadata", None) or {}
    if isinstance(metadata, dict):
        return (
            metadata.get("booking_id"),
            metadata.get("order_id"),
        )
    return (
        getattr(metadata, "booking_id", None),
        getattr(metadata, "order_id", None),
    )


def _parse_payment_intent_id(session: object) -> str | None:
    """Извлекает payment_intent id из Stripe session."""
    pi = getattr(session, "payment_intent", None)
    if pi is None and isinstance(session, dict):
        pi = session.get("payment_intent")
    if pi is None:
        return None
    return getattr(pi, "id", None) or (str(pi) if isinstance(pi, str) else None)


@router.post("/stripe", status_code=200)
async def stripe_webhook(request: Request) -> Response:
    """
    Обработчик Stripe webhook.

    Проверяет подпись, парсит событие checkout.session.completed,
    вызывает сервисы confirm_order_after_payment или confirm_booking_after_payment.
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

    if event.type != "checkout.session.completed":
        return Response(status_code=200)

    session = event.data.object
    booking_id_str, order_id_str = _parse_checkout_session_metadata(session)
    payment_intent_id = _parse_payment_intent_id(session)

    async with async_session_maker() as db_session:
        uow = create_uow(db_session)
        try:
            if order_id_str:
                try:
                    order_id = int(order_id_str)
                except ValueError:
                    return Response(status_code=200)
                ok = await confirm_order_after_payment(
                    uow,
                    order_id,
                    payment_intent_id=payment_intent_id,
                )
                if ok:
                    await uow.commit()
                    logger.info("Webhook: order_id=%s paid", order_id)
                else:
                    logger.warning("Webhook: order_id=%s not found or already paid", order_id)
                return Response(status_code=200)

            if booking_id_str:
                try:
                    booking_id = int(booking_id_str)
                except ValueError:
                    return Response(status_code=200)
                ok = await confirm_booking_after_payment(
                    uow,
                    booking_id,
                    payment_intent_id=payment_intent_id,
                )
                if ok:
                    await uow.commit()
                    logger.info("Webhook: booking_id=%s confirmed", booking_id)
                else:
                    logger.warning("Webhook: booking_id=%s not found or already confirmed", booking_id)
                return Response(status_code=200)

            logger.warning(
                "Webhook checkout.session.completed: missing metadata.booking_id and metadata.order_id"
            )
        except Exception:
            await uow.rollback()
            raise

    return Response(status_code=200)
