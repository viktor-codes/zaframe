from typing import TYPE_CHECKING

from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository

__all__ = ["OTPCodeRepository", "RefreshTokenRepository", "get_current_user_from_token"]

if TYPE_CHECKING:
    from app.modules.auth.service import get_current_user_from_token


def __getattr__(name: str):
    # WHY: service imports booking (legacy until tz-09); eager import here would cycle
    # with repositories/__init__ lazy-loading auth repos.
    if name == "get_current_user_from_token":
        from app.modules.auth.service import get_current_user_from_token

        return get_current_user_from_token
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
