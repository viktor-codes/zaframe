"""
JWT and OTP helpers.

PyJWT is used for JWT signing and verification because the previous JWT
library is unmaintained and affected by public parsing vulnerabilities.
"""

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import randbelow, token_urlsafe
from typing import Any

import jwt

from app.core.config import settings
from app.core.datetime_utils import utc_now


def _utcnow() -> datetime:
    """Return the current aware UTC timestamp."""
    return utc_now()


def create_access_token(
    user_id: int,
    email: str,
) -> str:
    """Create a short-lived access token."""
    now = _utcnow()
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_refresh_token(user_id: int) -> str:
    """
    Create a long-lived refresh token.

    The jti claim allows refresh-token rotation and per-session revocation.
    """
    now = _utcnow()
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = token_urlsafe(16)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": jti,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(  # pyright: ignore[reportUnknownMemberType]
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def decode_token(token: str) -> dict[str, Any] | None:
    """
    Decode and verify a JWT.

    Returns the payload or None for invalid/expired tokens.
    """
    try:
        payload = jwt.decode(  # pyright: ignore[reportUnknownMemberType]
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except jwt.PyJWTError:
        return None


def get_user_id_from_access_token(token: str) -> int | None:
    """Extract user_id from an access token."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        return None
    try:
        return int(payload["sub"])
    except (ValueError, KeyError):
        return None


def get_user_id_from_refresh_token(token: str) -> int | None:
    """Extract user_id from a refresh token."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None
    try:
        return int(payload["sub"])
    except (ValueError, KeyError):
        return None


@dataclass
class RefreshTokenData:
    """Structured refresh-token claims after validation."""

    user_id: int
    jti: str
    expires_at: datetime


def parse_refresh_token(token: str) -> RefreshTokenData | None:
    """
    Parse and validate a refresh token.

    Returns RefreshTokenData or None when the token is invalid.
    """
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh":
        return None

    try:
        user_id = int(payload["sub"])
        jti = str(payload["jti"])
        exp_raw = payload["exp"]
        exp_ts = float(exp_raw)
        expires_at = datetime.fromtimestamp(exp_ts, tz=UTC)
    except (KeyError, TypeError, ValueError):
        return None

    return RefreshTokenData(user_id=user_id, jti=jti, expires_at=expires_at)


def generate_otp_code() -> str:
    """Generate a numeric OTP (zero-padded to OTP_LENGTH digits)."""
    upper = 10**settings.OTP_LENGTH
    return str(randbelow(upper)).zfill(settings.OTP_LENGTH)


def create_csrf_token() -> str:
    """
    Create a CSRF token for double-submit cookie pattern.

    Random, unguessable token stored in a non-httpOnly cookie and echoed by the client
    in X-CSRF-Token header for sensitive cookie-auth endpoints.
    """
    return token_urlsafe(32)


def hash_otp_code(code: str) -> str:
    """
    HMAC-SHA256 hash of an OTP for storage in the database.

    Uses SECRET_KEY so a DB dump alone cannot recover plaintext codes.
    """
    key = settings.SECRET_KEY.encode("utf-8")
    msg = code.encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def verify_otp_code(code: str, stored_hash: str) -> bool:
    """Constant-time comparison of OTP plaintext against stored HMAC-SHA256 hash."""
    computed_hash = hash_otp_code(code)
    return hmac.compare_digest(stored_hash, computed_hash)


def get_otp_expires_at() -> datetime:
    """OTP expiry instant (aware UTC)."""
    return _utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
