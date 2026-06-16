"""Domain DTOs for course order booking (no Pydantic)."""

from __future__ import annotations

from dataclasses import dataclass

from app.models import Booking, Order
from app.modules.catalog.service import CourseAvailabilityDTO


@dataclass(frozen=True, slots=True)
class CourseBookingInput:
    service_id: int
    guest_name: str
    guest_email: str
    guest_phone: str | None


@dataclass(frozen=True, slots=True)
class CourseBookingResultDTO:
    order: Order
    bookings: list[Booking]
    availability: CourseAvailabilityDTO
