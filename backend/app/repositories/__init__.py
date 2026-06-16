# Repositories: entity queries, injected via UnitOfWork.

from app.modules.booking import BookingRepository
from app.modules.booking.order import OrderRepository
from app.modules.catalog import (
    OccurrenceRepository,
    ScheduleTemplateRepository,
    ServiceRepository,
    StudioRepository,
)
from app.modules.search import SearchRepository

__all__ = [
    "BookingRepository",
    "OrderRepository",
    "OTPCodeRepository",
    "RefreshTokenRepository",
    "ScheduleTemplateRepository",
    "SearchRepository",
    "ServiceRepository",
    "OccurrenceRepository",
    "StudioRepository",
    "UserRepository",
    "ProcessedWebhookEventRepository",
]


def __getattr__(name: str):
    # WHY: module repositories import repositories.base during package init;
    # eager import here would circular-import app.modules.*.
    if name in ("OTPCodeRepository", "RefreshTokenRepository"):
        from app.modules.auth.repository import OTPCodeRepository, RefreshTokenRepository

        return {
            "OTPCodeRepository": OTPCodeRepository,
            "RefreshTokenRepository": RefreshTokenRepository,
        }[name]
    if name == "ProcessedWebhookEventRepository":
        from app.modules.payment import ProcessedWebhookEventRepository

        return ProcessedWebhookEventRepository
    if name == "UserRepository":
        from app.modules.identity import UserRepository

        return UserRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
