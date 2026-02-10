# SQLAlchemy ORM models
# Все модели импортируются здесь для Alembic autogenerate

# Экспортируем Base для использования в моделях и Alembic
from app.core.database import Base

# Импортируем все модели для Alembic autogenerate
# Alembic должен видеть все модели через Base.metadata
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.guest_session import GuestSession
from app.models.slot import Slot
from app.models.studio import Studio
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.models.service import Service, ServiceType
from app.models.schedule import Schedule

__all__ = [
    "Base",
    "User",
    "Studio",
    "Slot",
    "Booking",
    "BookingStatus",
    "BookingType",
    "GuestSession",
    "Order",
    "OrderStatus",
    "Service",
    "ServiceType",
    "Schedule",
]
