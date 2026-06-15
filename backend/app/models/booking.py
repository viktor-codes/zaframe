"""
Модель Booking - бронирование слота клиентом.

Почему отдельная модель Booking:
- Один слот может быть забронирован несколькими клиентами
- Хранит информацию о конкретном бронировании (статус, оплата)
- Поддерживает гостевые бронирования (guest_email до OTP-верификации)

Статусы бронирования:
- pending: создано, ожидает оплаты
- confirmed: оплачено и подтверждено
- cancelled: отменено (клиентом или автоматически)
- expired: pending с истёкшим hold (reserved_until)
- completed: confirmed, слот уже завершился
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.mixins import TimestampMixin


class BookingStatus:
    """Статусы бронирования."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    COMPLETED = "completed"

    # WHY: only pending/confirmed block duplicate active bookings per slot+guest.
    ACTIVE_STATUSES: frozenset[str] = frozenset({PENDING, CONFIRMED})


class BookingType:
    """Тип бронирования."""

    SINGLE = "single"
    COURSE = "course"


class Booking(TimestampMixin, Base):
    """
    Бронирование слота клиентом.

    Может быть создано:
    1. Зарегистрированным пользователем (user_id)
    2. Гостем (guest_email) — user_id проставляется после OTP verify

    После успешной оплаты статус меняется на CONFIRMED.
    """

    __tablename__ = "bookings"
    __table_args__ = (
        Index(
            "uq_bookings_slot_guest_email_active",
            "slot_id",
            "guest_email",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'confirmed') AND guest_email IS NOT NULL"
            ),
        ),
        Index(
            "uq_bookings_slot_user_id_active",
            "slot_id",
            "user_id",
            unique=True,
            postgresql_where=text(
                "status IN ('pending', 'confirmed') AND user_id IS NOT NULL"
            ),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"), nullable=False, index=True)

    booking_type: Mapped[str] = mapped_column(
        String(20),
        default=BookingType.SINGLE,
        nullable=False,
        index=True,
    )
    service_id: Mapped[int | None] = mapped_column(
        ForeignKey("services.id"), nullable=True, index=True
    )
    order_id: Mapped[int | None] = mapped_column(ForeignKey("orders.id"), nullable=True, index=True)

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)

    guest_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    guest_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20), default=BookingStatus.PENDING, nullable=False, index=True
    )

    # WHY: pending must not hold capacity forever; expiry is driven by this timestamp.
    reserved_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    checkout_session_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )
    payment_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )

    unit_price_cents: Mapped[int | None] = mapped_column(nullable=True)

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    slot: Mapped[Slot] = relationship("Slot", back_populates="bookings")
    user: Mapped[User | None] = relationship("User", back_populates="bookings")
    service: Mapped[Service | None] = relationship(
        "Service",
        back_populates="bookings",
    )
    order: Mapped[Order | None] = relationship(
        "Order",
        back_populates="bookings",
    )

    def is_confirmed(self) -> bool:
        """Проверка, подтверждено ли бронирование."""
        return self.status == BookingStatus.CONFIRMED

    def is_pending(self) -> bool:
        """Проверка, ожидает ли бронирование оплаты."""
        return self.status == BookingStatus.PENDING

    def is_cancelled(self) -> bool:
        """Проверка, отменено ли бронирование."""
        return self.status == BookingStatus.CANCELLED

    def is_expired(self) -> bool:
        """Проверка, истекло ли ожидание оплаты."""
        return self.status == BookingStatus.EXPIRED

    def is_completed(self) -> bool:
        """Проверка, завершено ли бронирование после окончания слота."""
        return self.status == BookingStatus.COMPLETED
