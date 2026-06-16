# Repositories: entity queries, injected via UnitOfWork.

from app.modules.search import SearchRepository
from app.repositories.booking_repo import BookingRepository
from app.repositories.occurrence_repo import OccurrenceRepository
from app.repositories.order_repo import OrderRepository
from app.repositories.otp_code_repo import OTPCodeRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.schedule_template_repo import ScheduleTemplateRepository
from app.repositories.service_repo import ServiceRepository
from app.repositories.studio_repo import StudioRepository

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
    if name == "ProcessedWebhookEventRepository":
        from app.modules.payment import ProcessedWebhookEventRepository

        return ProcessedWebhookEventRepository
    if name == "UserRepository":
        from app.modules.identity import UserRepository

        return UserRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
