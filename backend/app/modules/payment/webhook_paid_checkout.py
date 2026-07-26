"""Checkout-session branch of Stripe webhook processing."""

from __future__ import annotations

import structlog

from app.core.uow import UnitOfWork
from app.modules.payment.service import (
    confirm_booking_after_payment,
    confirm_order_after_payment,
    record_checkout_completed_payment,
)
from app.modules.payment.webhook_handlers import record_processed_event
from app.modules.payment.webhook_parsing import (
    parse_amount_total,
    parse_checkout_session_id,
    parse_checkout_session_metadata,
    parse_currency,
    parse_payment_intent_id,
    parse_payment_status,
)


async def process_paid_checkout(
    uow: UnitOfWork,
    *,
    session: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> None:
    logger = structlog.get_logger(__name__)
    checkout_session_id = parse_checkout_session_id(session)
    if checkout_session_id is None:
        logger.warning(
            "webhook_checkout_missing_session_id",
            request_id=request_id,
            event_id=event_id,
            event_type=event_type,
            idempotency_outcome="ignored",
        )
        await record_processed_event(uow, event_id=event_id, event_type=event_type)
        return

    booking_id_str, order_id_str = parse_checkout_session_metadata(session)
    payment_intent_id = parse_payment_intent_id(session)
    amount_total = parse_amount_total(session)
    currency = parse_currency(session)
    payment_status = parse_payment_status(session, event_type=event_type)

    if order_id_str:
        try:
            order_id = int(order_id_str)
        except ValueError:
            logger.warning(
                "webhook_order_id_invalid",
                request_id=request_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="ignored",
            )
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            return
        ledger_ok = await record_checkout_completed_payment(
            uow,
            checkout_session_id=checkout_session_id,
            payment_intent_id=payment_intent_id,
            order_id=order_id,
            amount_cents=amount_total,
            currency=currency,
            payment_status=payment_status,
        )
        if not ledger_ok:
            return
        if payment_status != "paid":
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_order_payment_not_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
                event_type=event_type,
                payment_status=payment_status,
                idempotency_outcome="processed",
            )
            return
        ok = await confirm_order_after_payment(uow, order_id, payment_intent_id=payment_intent_id)
        if ok:
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_order_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="processed",
            )
        else:
            logger.warning(
                "webhook_order_not_found_or_already_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="unmatched",
            )
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
        return

    if booking_id_str:
        try:
            booking_id = int(booking_id_str)
        except ValueError:
            logger.warning(
                "webhook_booking_id_invalid",
                request_id=request_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="ignored",
            )
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            return
        ledger_ok = await record_checkout_completed_payment(
            uow,
            checkout_session_id=checkout_session_id,
            payment_intent_id=payment_intent_id,
            booking_id=booking_id,
            amount_cents=amount_total,
            currency=currency,
            payment_status=payment_status,
        )
        if not ledger_ok:
            return
        if payment_status != "paid":
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_booking_payment_not_paid",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
                event_type=event_type,
                payment_status=payment_status,
                idempotency_outcome="processed",
            )
            return
        ok = await confirm_booking_after_payment(
            uow,
            booking_id,
            payment_intent_id=payment_intent_id,
        )
        if ok:
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_booking_confirmed",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="processed",
            )
        else:
            logger.warning(
                "webhook_booking_not_found_or_already_confirmed",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
                event_type=event_type,
                idempotency_outcome="unmatched",
            )
            await record_processed_event(uow, event_id=event_id, event_type=event_type)
        return

    logger.warning(
        "webhook_checkout_completed_missing_metadata",
        request_id=request_id,
        event_id=event_id,
        event_type=event_type,
        idempotency_outcome="ignored",
    )
    await record_processed_event(uow, event_id=event_id, event_type=event_type)
