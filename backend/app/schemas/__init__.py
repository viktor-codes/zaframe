# Pydantic schemas for API request/response validation

from app.modules.search.schemas import SearchQueryParams, SearchResult
from app.schemas.booking import (
    BookingBase,
    BookingCancel,
    BookingCreate,
    BookingCreateAuthenticated,
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingResponseBase,
    BookingSelfListItem,
    BookingSelfResponse,
    BookingWithOccurrence,
    BookingWithUser,
)
from app.schemas.catalog import PublicOccurrence, PublicService, StudioPublicResponse
from app.schemas.occurrence import (
    OccurrenceBase,
    OccurrenceCreate,
    OccurrenceResponse,
    OccurrenceUpdate,
    OccurrenceWithBookings,
)
from app.schemas.order import (
    CourseAvailabilityResult,
    CourseBookingCreate,
    CourseBookingPreviewItem,
    CourseBookingResponse,
    OrderBase,
    OrderResponse,
)
from app.schemas.payment import (
    CheckoutSessionCreate,
    CheckoutSessionResponse,
    OrderCheckoutSessionCreate,
)
from app.schemas.schedule import (
    ScheduleGenerateRequest,
    ScheduleTemplateBase,
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
)
from app.schemas.service import (
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
    ServiceBase,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.schemas.studio import (
    StudioBase,
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    StudioWithOccurrences,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserPublic,
    UserResponse,
    UserUpdate,
)

# Rebuild models with forward references before use in unions.
BookingSelfResponse.model_rebuild()
BookingCreatedResponse.model_rebuild()
BookingOwnerResponse.model_rebuild()
BookingWithUser.model_rebuild()
BookingSelfListItem.model_rebuild()
CourseBookingResponse.model_rebuild()
SearchResult.model_rebuild()

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
    "StudioWithOccurrences",
    "StudioPublicResponse",
    # Occurrence
    "OccurrenceBase",
    "OccurrenceCreate",
    "OccurrenceUpdate",
    "OccurrenceResponse",
    "OccurrenceWithBookings",
    # Booking
    "BookingBase",
    "BookingCreate",
    "BookingCreateAuthenticated",
    "BookingResponseBase",
    "BookingSelfResponse",
    "BookingCreatedResponse",
    "BookingOwnerResponse",
    "BookingWithOccurrence",
    "BookingWithUser",
    "BookingSelfListItem",
    "BookingCancel",
    # ScheduleTemplate template / generation
    "ScheduleTemplateBase",
    "ScheduleTemplateCreate",
    "ScheduleTemplateResponse",
    "ScheduleGenerateRequest",
    # Service
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceAvailabilityScheduleItem",
    "ServiceAvailabilityResponse",
    # Order / course purchase
    "OrderBase",
    "OrderResponse",
    "CourseBookingCreate",
    "CourseBookingResponse",
    "CourseAvailabilityResult",
    "CourseBookingPreviewItem",
    # Catalog (public)
    "PublicService",
    "PublicOccurrence",
    # Payments
    "CheckoutSessionCreate",
    "OrderCheckoutSessionCreate",
    "CheckoutSessionResponse",
    # Search
    "SearchQueryParams",
    "SearchResult",
]
