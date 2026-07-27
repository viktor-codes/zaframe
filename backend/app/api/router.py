"""Aggregate all domain routers and finalize Pydantic forward references."""

from fastapi import APIRouter, FastAPI

from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.modules.auth.router import account_router
from app.modules.auth.router import router as auth_router
from app.modules.booking.order import CourseBookingResponse, OrderListItem
from app.modules.booking.order.router import router as order_router
from app.modules.booking.router import create_router as booking_create_router
from app.modules.booking.router import occurrence_bookings_router
from app.modules.booking.router import owner_router as booking_owner_router
from app.modules.booking.router import router as booking_router
from app.modules.booking.schemas import (
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
    BookingWithUser,
)
from app.modules.catalog.occurrence.list_router import list_router as occurrence_list_router
from app.modules.catalog.occurrence.router import router as occurrence_router
from app.modules.catalog.occurrence.studio_occurrence_router import studio_occurrence_router
from app.modules.catalog.public.router import public_router
from app.modules.catalog.schedule.router import schedule_router
from app.modules.catalog.service.router import router as service_router
from app.modules.catalog.service.schedule_templates_router import schedule_templates_router
from app.modules.catalog.service.studio_services_router import studio_services_router
from app.modules.catalog.studio.list_router import list_router as studio_list_router
from app.modules.catalog.studio.members_router import router as studio_members_router
from app.modules.catalog.studio.router import router as studio_router
from app.modules.payment.router import router as payment_router
from app.modules.payment.studio_router import studio_payment_router
from app.modules.payment.webhooks import router as webhooks_router
from app.modules.search import SearchResult
from app.modules.search.router import router as search_router

# Rebuild models with forward references before use in unions.
BookingSelfResponse.model_rebuild()
BookingCreatedResponse.model_rebuild()
BookingOwnerResponse.model_rebuild()
BookingWithUser.model_rebuild()
BookingSelfListItem.model_rebuild()
CourseBookingResponse.model_rebuild()
OrderListItem.model_rebuild()
SearchResult.model_rebuild()

api_v1 = APIRouter(prefix="/api/v1")
for r in (
    public_router,
    studio_list_router,
    studio_router,
    studio_services_router,
    studio_members_router,
    studio_occurrence_router,
    schedule_router,
    service_router,
    schedule_templates_router,
    occurrence_list_router,
    occurrence_router,
    booking_create_router,
    booking_router,
    booking_owner_router,
    occurrence_bookings_router,
    order_router,
    payment_router,
    studio_payment_router,
    auth_router,
    account_router,
    search_router,
):
    api_v1.include_router(r)


def register_routers(app: FastAPI) -> None:
    """Wire health, versioned API, and webhook routes onto the FastAPI app."""
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(metrics_router)
    app.include_router(api_v1)
    app.include_router(webhooks_router)
