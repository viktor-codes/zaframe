# Pydantic schemas для валидации входных/выходных данных API

from app.schemas.booking import (
    BookingBase,
    BookingCancel,
    BookingCreate,
    BookingCreateAuthenticated,
    BookingResponse,
    BookingUpdate,
    BookingWithSlot,
    BookingWithUser,
)
from app.schemas.guest_session import (
    GuestSessionBase,
    GuestSessionCreate,
    GuestSessionResponse,
)
from app.schemas.slot import (
    SlotBase,
    SlotCreate,
    SlotResponse,
    SlotUpdate,
    SlotWithBookings,
)
from app.schemas.studio import (
    StudioBase,
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    StudioWithSlots,
)
from app.schemas.service import (
    CourseAvailabilityResult,
    CourseBookingCreate,
    CourseBookingResponse,
    CourseBookingPreviewItem,
    OrderBase,
    OrderResponse,
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
    PublicService,
    PublicServiceOccurrence,
    ScheduleBase,
    ScheduleCreate,
    ScheduleResponse,
    ServiceBase,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    StudioPublicResponse,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserPublic,
    UserResponse,
    UserUpdate,
)
from app.schemas.payment import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
)
from app.schemas.search import SearchQueryParams, SearchResult

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPublic",
    # Studio
    "StudioBase",
    "StudioCreate",
    "StudioUpdate",
    "StudioResponse",
    "StudioWithSlots",
    "StudioPublicResponse",
    # Slot
    "SlotBase",
    "SlotCreate",
    "SlotUpdate",
    "SlotResponse",
    "SlotWithBookings",
    # Booking
    "BookingBase",
    "BookingCreate",
    "BookingCreateAuthenticated",
    "BookingUpdate",
    "BookingResponse",
    "BookingWithSlot",
    "BookingWithUser",
    "BookingCancel",
    # Service / Schedule / Order / Public
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ScheduleBase",
    "ScheduleCreate",
    "ScheduleResponse",
    "OrderBase",
    "OrderResponse",
    "ServiceAvailabilityScheduleItem",
    "ServiceAvailabilityResponse",
    "CourseBookingCreate",
    "CourseBookingResponse",
    "CourseAvailabilityResult",
    "CourseBookingPreviewItem",
    "PublicService",
    "PublicServiceOccurrence",
    "StudioPublicResponse",
    # Payments
    "CheckoutSessionCreate",
    "OrderCheckoutSessionCreate",
    "CheckoutSessionResponse",
    # GuestSession
    "GuestSessionBase",
    "GuestSessionCreate",
    "GuestSessionResponse",
    # Search
    "SearchQueryParams",
    "SearchResult",
]
