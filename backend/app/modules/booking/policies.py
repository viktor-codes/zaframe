"""Pure booking access policies (published cross-domain surface)."""

from app.models.booking import Booking
from app.models.user import User


def is_own_booking(booking: Booking, user: User) -> bool:
    """True when booking belongs to the user (by user_id or guest_email)."""
    if booking.user_id is not None and booking.user_id == user.id:
        return True
    if booking.guest_email is not None:
        return booking.guest_email.strip().lower() == user.email.strip().lower()
    return False


def can_access_booking(
    booking: Booking,
    user: User,
    *,
    studio_owner_id: int | None,
) -> bool:
    """True when booking is the user's own or belongs to a studio they own."""
    if is_own_booking(booking, user):
        return True
    return studio_owner_id is not None and studio_owner_id == user.id
