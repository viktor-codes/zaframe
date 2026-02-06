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
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserPublic,
    UserResponse,
    UserUpdate,
)

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
    # GuestSession
    "GuestSessionBase",
    "GuestSessionCreate",
    "GuestSessionResponse",
]
