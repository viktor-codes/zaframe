"""Compatibility shim — re-exports payment service functions for existing imports."""

from app.modules.payment.access import is_own_order
from app.modules.payment.capacity import PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
from app.modules.payment.checkout import create_checkout_session, create_order_checkout_session
from app.modules.payment.confirmation import (
    PAYMENT_STATUS_SUCCEEDED,
    confirm_booking_after_payment,
    confirm_order_after_payment,
)

__all__ = [
    "PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW",
    "PAYMENT_STATUS_SUCCEEDED",
    "confirm_booking_after_payment",
    "confirm_order_after_payment",
    "create_checkout_session",
    "create_order_checkout_session",
    "is_own_order",
]
