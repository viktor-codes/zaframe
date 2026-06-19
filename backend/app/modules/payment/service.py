"""Compatibility shim — re-exports payment service functions for existing imports."""

from app.modules.payment.access import is_own_order
from app.modules.payment.capacity import PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
from app.modules.payment.checkout import create_checkout_session, create_order_checkout_session
from app.modules.payment.confirmation import (
    PAYMENT_STATUS_SUCCEEDED,
    confirm_booking_after_payment,
    confirm_order_after_payment,
)
from app.modules.payment.connect import (
    create_stripe_onboarding_link,
    get_stripe_connect_status,
    refresh_stripe_connect_status,
    update_studio_connect_status_from_account,
)
from app.modules.payment.ledger import list_studio_payments, record_checkout_completed_payment
from app.modules.payment.refunds import (
    create_refund_for_payment,
    get_payment_or_raise,
    get_payment_studio_or_raise,
    update_refund_from_stripe_object,
)

__all__ = [
    "PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW",
    "PAYMENT_STATUS_SUCCEEDED",
    "confirm_booking_after_payment",
    "confirm_order_after_payment",
    "create_refund_for_payment",
    "create_checkout_session",
    "create_order_checkout_session",
    "create_stripe_onboarding_link",
    "get_payment_or_raise",
    "get_payment_studio_or_raise",
    "get_stripe_connect_status",
    "is_own_order",
    "list_studio_payments",
    "record_checkout_completed_payment",
    "refresh_stripe_connect_status",
    "update_studio_connect_status_from_account",
    "update_refund_from_stripe_object",
]
