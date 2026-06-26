"""Payment access checks for checkout, refunds, and studio payouts."""

from __future__ import annotations

import structlog

from app.core.access_tokens import verify_resource_access_token
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.booking import Booking
from app.models.order import Order
from app.models.studio import Studio
from app.models.studio_member import StudioMemberRole
from app.models.user import User
from app.modules.booking.policies import is_own_booking
from app.modules.identity.policies import is_owned_by_user

logger = structlog.get_logger(__name__)


def is_own_order(order: Order, user: User) -> bool:
    """True when order belongs to the user (by user_id or guest_email)."""
    return is_owned_by_user(
        user=user,
        user_id=order.user_id,
        guest_email=order.guest_email,
    )


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


async def require_studio_payout_permission(
    uow: UnitOfWork,
    *,
    studio: Studio,
    user: User,
) -> None:
    """Raise ForbiddenError unless user can manage payouts for the studio."""
    membership = await uow.studio_members.get_by_studio_and_user(
        studio_id=studio.id,
        user_id=user.id,
    )
    role = membership.role if membership is not None else None
    if role is None and studio.owner_id == user.id:
        role = StudioMemberRole.OWNER.value

    if role in {StudioMemberRole.OWNER.value, StudioMemberRole.MANAGER.value}:
        return

    log_domain_event(
        logger,
        "permission_denied",
        level="warning",
        user_id=user.id,
        studio_id=studio.id,
        permission="manage_payouts",
    )
    raise ForbiddenError("Access denied for this studio")
