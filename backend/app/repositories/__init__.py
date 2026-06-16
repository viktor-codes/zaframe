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
from app.repositories.user_repo import UserRepository

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
    # WHY: payment.repository imports repositories.base during package init;
    # eager import here would circular-import app.modules.payment.
    if name == "ProcessedWebhookEventRepository":
        from app.modules.payment import ProcessedWebhookEventRepository

        return ProcessedWebhookEventRepository
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
