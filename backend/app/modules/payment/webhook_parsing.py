"""Stripe webhook payload parsing helpers."""

from __future__ import annotations

from typing import cast


def _object_value(source: object, key: str) -> object:
    if isinstance(source, dict):
        return cast(dict[str, object], source).get(key)
    return getattr(source, key, None)


def _metadata_value(metadata: object, key: str) -> str | None:
    raw = _object_value(metadata, key)
    if raw is None:
        return None
    return str(raw)


def parse_checkout_session_metadata(session: object) -> tuple[str | None, str | None]:
    """Extract booking_id and order_id from Stripe Checkout Session metadata."""
    metadata: object = _object_value(session, "metadata") or {}
    return (
        _metadata_value(metadata, "booking_id"),
        _metadata_value(metadata, "order_id"),
    )


def parse_payment_intent_id(session: object) -> str | None:
    """Extract PaymentIntent id from a Stripe Checkout Session."""
    pi = _object_value(session, "payment_intent")
    if pi is None:
        return None
    if isinstance(pi, str):
        return pi
    pi_id = _object_value(pi, "id") or pi
    return str(pi_id)


def parse_checkout_session_id(session: object) -> str | None:
    value = _object_value(session, "id")
    if value is None:
        return None
    return str(value)


def parse_amount_total(session: object) -> int | None:
    value = _object_value(session, "amount_total")
    if isinstance(value, int):
        return value
    return None


def parse_currency(session: object) -> str | None:
    value = _object_value(session, "currency")
    if value is None:
        return None
    return str(value)


def parse_payment_status(session: object, *, event_type: str) -> str:
    if event_type == "checkout.session.async_payment_succeeded":
        return "paid"
    if event_type == "checkout.session.async_payment_failed":
        return "failed"
    value = _object_value(session, "payment_status")
    if value is None:
        return "unpaid"
    return str(value)
