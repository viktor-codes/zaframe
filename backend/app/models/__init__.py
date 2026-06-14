# SQLAlchemy ORM models
# Все модели импортируются здесь для Alembic autogenerate

from app.core.database import Base

from app.models.booking import Booking, BookingStatus, BookingType
from app.models.order import Order, OrderStatus
from app.models.otp_code import OTPCode
from app.models.refresh_token import RefreshToken
from app.models.schedule import Schedule
from app.models.service import Service, ServiceCategory, ServiceType
from app.models.slot import Slot, SlotStatus
from app.models.studio import Studio
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Studio",
    "Slot",
    "SlotStatus",
    "Booking",
    "BookingStatus",
    "BookingType",
    "OTPCode",
    "Order",
    "OrderStatus",
    "Service",
    "ServiceType",
    "ServiceCategory",
    "Schedule",
    "RefreshToken",
]
