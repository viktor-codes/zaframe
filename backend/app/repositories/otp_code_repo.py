"""
Repository for OTPCode entities (email OTP authentication).
"""

from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.otp_code import OTPCode
from app.repositories.base import WriteRepositoryMixin


class OTPCodeRepository(WriteRepositoryMixin):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_recent_requests(self, email: str, since: datetime) -> int:
        """Count OTP request rows for rate limiting (includes invalidated codes)."""
        result = await self._session.execute(
            select(func.count())
            .select_from(OTPCode)
            .where(
                OTPCode.email == email,
                OTPCode.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def invalidate_active_for_email(self, email: str, now: datetime) -> None:
        """Mark all unused non-expired codes for email as used (superseded by new request)."""
        await self._session.execute(
            update(OTPCode)
            .where(
                OTPCode.email == email,
                OTPCode.used_at.is_(None),
                OTPCode.expires_at > now,
            )
            .values(used_at=now)
        )
        await self._session.flush()

    async def get_latest_active_for_email(self, email: str, now: datetime) -> OTPCode | None:
        """Latest unused non-expired OTP for email (verify wrong-code attempts)."""
        result = await self._session.execute(
            select(OTPCode)
            .where(
                OTPCode.email == email,
                OTPCode.used_at.is_(None),
                OTPCode.expires_at > now,
            )
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def delete_expired_before(self, before: datetime) -> int:
        """Delete OTP rows with expires_at older than `before`. Returns rows removed."""
        from sqlalchemy import delete

        result = await self._session.execute(
            delete(OTPCode).where(OTPCode.expires_at < before)
        )
        await self._session.flush()
        return result.rowcount or 0
