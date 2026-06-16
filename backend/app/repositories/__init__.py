# Repositories: entity queries, injected via UnitOfWork.

from app.modules.catalog import (
    OccurrenceRepository,
    ScheduleTemplateRepository,
    ServiceRepository,
    StudioRepository,
)
from app.modules.search import SearchRepository
from app.repositories.booking_repo import BookingRepository
from app.repositories.order_repo import OrderRepository

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
