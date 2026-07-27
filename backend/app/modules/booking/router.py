"""Booking HTTP routers — compatibility re-exports for api registration."""

from app.modules.booking.create_router import create_router
from app.modules.booking.customer_router import router
from app.modules.booking.occurrence_bookings_router import occurrence_bookings_router
from app.modules.booking.owner_router import owner_router

__all__ = [
    "create_router",
    "occurrence_bookings_router",
    "owner_router",
    "router",
]
