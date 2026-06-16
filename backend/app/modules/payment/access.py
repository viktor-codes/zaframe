"""Checkout access checks for bookings and orders."""

from __future__ import annotations

from app.core.access_tokens import verify_resource_access_token
from app.core.exceptions import NotFoundError
from app.models.booking import Booking
from app.models.order import Order
from app.models.user import User
from app.modules.booking.policies import is_own_booking


def is_own_order(order: Order, user: User) -> bool:
    """True when order belongs to the user (by user_id or guest_email)."""
    if order.user_id is not None and order.user_id == user.id:
        return True
    if order.guest_email is not None:
        return order.guest_email.strip().lower() == user.email.strip().lower()
    return False


def assert_booking_checkout_access(
    booking: Booking,
    *,
    current_user: User | None,
    access_token: str | None,
) -> None:
    """Allow owner auth or valid guest token; otherwise 404 (no resource enumeration)."""
    if current_user is not None and is_own_booking(booking, current_user):
        return
    if verify_resource_access_token(booking.access_token, access_token):
        return
    raise NotFoundError("Booking not found")


def assert_order_checkout_access(
    order: Order,
    *,
    current_user: User | None,
    access_token: str | None,
) -> None:
    """Allow owner auth or valid guest token; otherwise 404 (no resource enumeration)."""
    if current_user is not None and is_own_order(order, current_user):
        return
    if verify_resource_access_token(order.access_token, access_token):
        return
    raise NotFoundError("Order not found")
