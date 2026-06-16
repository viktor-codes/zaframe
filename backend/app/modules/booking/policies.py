"""Pure booking access policies (published cross-domain surface)."""

from app.models.booking import Booking
from app.models.user import User
from app.modules.identity.policies import is_owned_by_user


def is_own_booking(booking: Booking, user: User) -> bool:
    """True when booking belongs to the user (by user_id or guest_email)."""
    return is_owned_by_user(
        user=user,
        user_id=booking.user_id,
        guest_email=booking.guest_email,
    )


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
