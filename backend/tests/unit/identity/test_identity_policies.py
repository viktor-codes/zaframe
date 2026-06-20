"""Unit tests for canonical user-ownership policy."""

from app.models.user import User
from app.modules.identity.policies import is_owned_by_user


def _user(*, user_id: int = 1, email: str = "owner@example.com") -> User:
    return User(id=user_id, email=email, name="Owner")


def test_is_owned_by_user_when_user_id_matches() -> None:
    user = _user(user_id=42)

    assert is_owned_by_user(user=user, user_id=42, guest_email=None) is True


def test_is_owned_by_user_when_guest_email_matches_case_insensitive() -> None:
    user = _user(email="Owner@Example.COM")

    assert is_owned_by_user(user=user, user_id=None, guest_email="  owner@example.com  ") is True


def test_is_owned_by_user_when_neither_matches() -> None:
    user = _user(user_id=1, email="me@example.com")

    assert is_owned_by_user(user=user, user_id=99, guest_email="other@example.com") is False


def test_is_owned_by_user_when_both_none() -> None:
    user = _user()

    assert is_owned_by_user(user=user, user_id=None, guest_email=None) is False
