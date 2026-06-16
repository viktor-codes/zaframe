"""Canonical user-ownership rules shared across domains."""

from app.models.user import User


def is_owned_by_user(
    *,
    user: User,
    user_id: int | None,
    guest_email: str | None,
) -> bool:
    """True when resource is linked by user_id or guest_email (case-insensitive)."""
    if user_id is not None and user_id == user.id:
        return True
    if guest_email is not None:
        return guest_email.strip().lower() == user.email.strip().lower()
    return False
