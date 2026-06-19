"""Stripe webhook processing use-cases."""

from __future__ import annotations

from typing import Any, cast

import structlog
from sqlalchemy.exc import IntegrityError

from app.core.uow import UnitOfWork
from app.modules.payment.service import (
    confirm_booking_after_payment,
    confirm_order_after_payment,
    record_checkout_completed_payment,
    update_refund_from_stripe_object,
    update_studio_connect_status_from_account,
)

_CHECKOUT_SUCCESS_EVENTS = frozenset(
    {"checkout.session.completed", "checkout.session.async_payment_succeeded"}
)
_CHECKOUT_FAILED_EVENTS = frozenset({"checkout.session.async_payment_failed"})
_SUPPORTED_EVENTS = _CHECKOUT_SUCCESS_EVENTS | _CHECKOUT_FAILED_EVENTS | {
    "account.updated",
    "refund.updated",
}


def _object_value(source: object, key: str) -> object:
    if isinstance(source, dict):
        return cast(dict[str, object], source).get(key)
    return getattr(source, key, None)


def _metadata_value(metadata: object, key: str) -> str | None:
    raw = _object_value(metadata, key)
    if raw is None:
        return None
    return str(raw)


def _parse_checkout_session_metadata(session: object) -> tuple[str | None, str | None]:
    """Extract booking_id and order_id from Stripe Checkout Session metadata."""
    metadata: object = _object_value(session, "metadata") or {}
    return (
        _metadata_value(metadata, "booking_id"),
        _metadata_value(metadata, "order_id"),
    )


def _parse_payment_intent_id(session: object) -> str | None:
    """Extract PaymentIntent id from a Stripe Checkout Session."""
    pi = _object_value(session, "payment_intent")
    if pi is None:
        return None
    if isinstance(pi, str):
        return pi
    pi_id = _object_value(pi, "id") or pi
    return str(pi_id)


def _parse_checkout_session_id(session: object) -> str | None:
    value = _object_value(session, "id")
    if value is None:
        return None
    return str(value)


def _parse_amount_total(session: object) -> int | None:
    value = _object_value(session, "amount_total")
    if isinstance(value, int):
        return value
    return None


def _parse_currency(session: object) -> str | None:
    value = _object_value(session, "currency")
    if value is None:
        return None
    return str(value)


def _parse_payment_status(session: object, *, event_type: str) -> str:
    if event_type == "checkout.session.async_payment_succeeded":
        return "paid"
    if event_type == "checkout.session.async_payment_failed":
        return "failed"
    value = _object_value(session, "payment_status")
    if value is None:
        return "unpaid"
    return str(value)


async def _record_processed_event(uow: UnitOfWork, *, event_id: str, event_type: str) -> None:
    await uow.webhook_events.record(event_id=event_id, event_type=event_type)
    await uow.commit()


async def _process_account_updated(
    uow: UnitOfWork,
    *,
    account: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> None:
    logger = structlog.get_logger(__name__)
    ok = await update_studio_connect_status_from_account(uow, account=account)
    if ok:
        await _record_processed_event(uow, event_id=event_id, event_type=event_type)
        logger.info("webhook_stripe_account_updated", request_id=request_id, event_id=event_id)
        return
    logger.warning(
        "webhook_stripe_account_updated_unmatched",
        request_id=request_id,
        event_id=event_id,
    )


async def _process_refund_updated(
    uow: UnitOfWork,
    *,
    stripe_refund: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> None:
    logger = structlog.get_logger(__name__)
    ok = await update_refund_from_stripe_object(uow, stripe_refund=stripe_refund)
    if ok:
        await _record_processed_event(uow, event_id=event_id, event_type=event_type)
        logger.info("webhook_refund_updated", request_id=request_id, event_id=event_id)
        return
    logger.warning("webhook_refund_updated_unmatched", request_id=request_id, event_id=event_id)


async def _process_paid_checkout(
    uow: UnitOfWork,
    *,
    session: object,
    event_id: str,
    event_type: str,
    request_id: str | None,
) -> None:
    logger = structlog.get_logger(__name__)
    checkout_session_id = _parse_checkout_session_id(session)
    if checkout_session_id is None:
        logger.warning("webhook_checkout_missing_session_id", request_id=request_id, event_id=event_id)
        return

    booking_id_str, order_id_str = _parse_checkout_session_metadata(session)
    payment_intent_id = _parse_payment_intent_id(session)
    amount_total = _parse_amount_total(session)
    currency = _parse_currency(session)
    payment_status = _parse_payment_status(session, event_type=event_type)

    if order_id_str:
        try:
            order_id = int(order_id_str)
        except ValueError:
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
            await _record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_order_payment_not_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
                payment_status=payment_status,
            )
            return
        ok = await confirm_order_after_payment(uow, order_id, payment_intent_id=payment_intent_id)
        if ok:
            await _record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_order_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
            )
        else:
            logger.warning(
                "webhook_order_not_found_or_already_paid",
                request_id=request_id,
                order_id=order_id,
                event_id=event_id,
            )
        return

    if booking_id_str:
        try:
            booking_id = int(booking_id_str)
        except ValueError:
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
            await _record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_booking_payment_not_paid",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
                payment_status=payment_status,
            )
            return
        ok = await confirm_booking_after_payment(
            uow,
            booking_id,
            payment_intent_id=payment_intent_id,
        )
        if ok:
            await _record_processed_event(uow, event_id=event_id, event_type=event_type)
            logger.info(
                "webhook_booking_confirmed",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
            )
        else:
            logger.warning(
                "webhook_booking_not_found_or_already_confirmed",
                request_id=request_id,
                booking_id=booking_id,
                event_id=event_id,
            )
        return

    logger.warning("webhook_checkout_completed_missing_metadata", request_id=request_id, event_id=event_id)


async def process_stripe_webhook_event(
    uow: UnitOfWork,
    *,
    event: Any,
    request_id: str | None = None,
) -> None:
    """Process supported Stripe webhook events idempotently."""
    logger = structlog.get_logger(__name__)
    event_id = str(event.id)
    event_type = str(event.type)
    if event_type not in _SUPPORTED_EVENTS:
        return

    try:
        if await uow.webhook_events.exists_by_event_id(event_id):
            logger.info("webhook_duplicate_event_skipped", request_id=request_id, event_id=event_id)
            return

        if event_type == "account.updated":
            await _process_account_updated(
                uow,
                account=event.data.object,
                event_id=event_id,
                event_type=event_type,
                request_id=request_id,
            )
            return

        if event_type == "refund.updated":
            await _process_refund_updated(
                uow,
                stripe_refund=event.data.object,
                event_id=event_id,
                event_type=event_type,
                request_id=request_id,
            )
            return

        await _process_paid_checkout(
            uow,
            session=event.data.object,
            event_id=event_id,
            event_type=event_type,
            request_id=request_id,
        )
    except IntegrityError:
        await uow.rollback()
        logger.info("webhook_duplicate_event_race", request_id=request_id, event_id=event_id)
    except Exception:
        await uow.rollback()
        raise
