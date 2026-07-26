"""
Authentication business logic: email OTP and JWT sessions.

Thin re-export shim so existing `app.modules.auth.service` imports keep working.
"""

from app.modules.auth.otp import request_otp, verify_otp
from app.modules.auth.sessions import (
    get_current_user_from_token,
    logout_current_session,
    refresh_access_token,
)

__all__ = [
    "request_otp",
    "verify_otp",
    "refresh_access_token",
    "get_current_user_from_token",
    "logout_current_session",
]
