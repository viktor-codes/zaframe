"""GDPR data export (DSAR) for the authenticated account."""

from __future__ import annotations

from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.identity.schemas import (
    BookingExportItem,
    OrderExportItem,
    PaymentExportItem,
    UserDataExportResponse,
    UserExportItem,
)

# WHY: DSAR should be complete for closed-beta volumes; hard cap avoids unbounded payloads.
_EXPORT_LIMIT = 500


async def export_current_user_data(uow: UnitOfWork, user: User) -> UserDataExportResponse:
    """Assemble user + bookings + orders + payments for the current account."""
    bookings = await uow.bookings.list_my_with_occurrence_and_studio(
        skip=0,
        limit=_EXPORT_LIMIT,
        user_id=user.id,
        user_email=user.email,
        include_guest_email=True,
    )
    orders = await uow.orders.list_for_user(
        user_id=user.id,
        user_email=user.email,
        skip=0,
        limit=_EXPORT_LIMIT,
    )
    payments = await uow.payments.list_for_user(
        user_id=user.id,
        user_email=user.email,
        skip=0,
        limit=_EXPORT_LIMIT,
    )
    return UserDataExportResponse(
        user=UserExportItem.model_validate(user),
        bookings=[BookingExportItem.model_validate(b) for b in bookings],
        orders=[OrderExportItem.model_validate(o) for o in orders],
        payments=[PaymentExportItem.model_validate(p) for p in payments],
    )
