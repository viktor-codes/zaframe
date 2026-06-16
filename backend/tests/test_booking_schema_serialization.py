"""Serialization snapshots for client-facing booking response schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.modules.booking.schemas import (
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
)

_FIXED_NOW = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)

_SELF_SNAPSHOT = {
    "occurrence_id": 10,
    "id": 1,
    "user_id": None,
    "status": "pending",
    "reserved_until": _FIXED_NOW.isoformat().replace("+00:00", "Z"),
    "payment_status": "unpaid",
    "created_at": _FIXED_NOW.isoformat().replace("+00:00", "Z"),
    "updated_at": _FIXED_NOW.isoformat().replace("+00:00", "Z"),
    "cancelled_at": None,
    "is_guest_booking": True,
    "guest_name": "Guest User",
    "guest_email": "guest@example.com",
    "guest_phone": "+111111111",
}

_OWNER_SNAPSHOT = {
    "occurrence_id": 10,
    "id": 1,
    "user_id": None,
    "status": "confirmed",
    "reserved_until": None,
    "payment_status": "paid",
    "created_at": _FIXED_NOW.isoformat().replace("+00:00", "Z"),
    "updated_at": _FIXED_NOW.isoformat().replace("+00:00", "Z"),
    "cancelled_at": None,
    "is_guest_booking": True,
    "guest_name": "Guest User",
    "guest_email": "guest@example.com",
    "guest_phone": "+111111111",
}

_STRIPE_INTERNAL_FIELDS = frozenset({"payment_intent_id", "checkout_session_id", "access_token"})


def _booking_orm(**overrides: object) -> SimpleNamespace:
    """Minimal ORM-like object with Stripe internals that must not leak to clients."""
    data = {
        "occurrence_id": 10,
        "id": 1,
        "user_id": None,
        "guest_name": "Guest User",
        "guest_email": "guest@example.com",
        "guest_phone": "+111111111",
        "status": "pending",
        "reserved_until": _FIXED_NOW,
        "checkout_session_id": "cs_secret_123",
        "payment_intent_id": "pi_secret_456",
        "access_token": "secret-guest-token",
        "payment_status": "unpaid",
        "created_at": _FIXED_NOW,
        "updated_at": _FIXED_NOW,
        "cancelled_at": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


@pytest.mark.parametrize(
    ("schema_cls", "expected_snapshot"),
    [
        (BookingSelfResponse, _SELF_SNAPSHOT),
        (BookingOwnerResponse, _OWNER_SNAPSHOT),
    ],
)
def test_booking_client_schema_serialization_snapshot(schema_cls, expected_snapshot):
    """Client schemas must serialize a stable field set without Stripe internals."""
    booking = _booking_orm(
        status=expected_snapshot["status"],
        payment_status=expected_snapshot["payment_status"],
        reserved_until=(_FIXED_NOW if expected_snapshot["reserved_until"] is not None else None),
    )
    payload = schema_cls.model_validate(booking).model_dump(mode="json")

    assert payload == expected_snapshot
    assert _STRIPE_INTERNAL_FIELDS.isdisjoint(payload.keys())


def test_booking_self_list_item_omits_stripe_internal_fields():
    """Cabinet list schema must not declare Stripe internal payment fields."""
    field_names = set(BookingSelfListItem.model_fields.keys())
    assert _STRIPE_INTERNAL_FIELDS.isdisjoint(field_names)

    booking = _booking_orm()
    self_payload = BookingSelfResponse.model_validate(booking).model_dump(mode="json")
    assert _STRIPE_INTERNAL_FIELDS.isdisjoint(self_payload.keys())
