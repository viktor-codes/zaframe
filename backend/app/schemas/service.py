"""
Pydantic схемы для Service, Schedule и Order.
"""
from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, EmailStr, Field

from app.models import BookingType, OrderStatus, ServiceType, ServiceCategory


class ServiceBase(BaseModel):
    """Базовые поля услуги."""

    name: str = Field(..., min_length=1, max_length=200, description="Название услуги")
    description: str | None = Field(
        None,
        max_length=1000,
        description="Описание услуги",
    )
    type: str = Field(
        default=ServiceType.SINGLE_CLASS,
        description="Тип услуги: single_class или course",
    )
    category: ServiceCategory = Field(
        default=ServiceCategory.YOGA,
        description="Категория услуги (йога, бокс, танцы и т.д.)",
    )
    duration_minutes: int = Field(..., ge=1, description="Длительность занятия в минутах")
    max_capacity: int = Field(..., ge=1, description="Максимальное количество мест")
    price_single_cents: int = Field(
        ...,
        ge=0,
        description="Цена за одно занятие (drop‑in) в центах",
    )
    price_course_cents: int | None = Field(
        None,
        ge=0,
        description="Цена за курс (если type=course) в центах",
    )
    soft_limit_ratio: float = Field(
        1.0,
        ge=1.0,
        le=2.0,
        description="Соотношение soft‑лимита к max_capacity (обычно 1.0–1.2)",
    )
    hard_limit_ratio: float = Field(
        1.5,
        ge=1.0,
        le=3.0,
        description="Соотношение hard‑лимита к max_capacity (жёсткий предел)",
    )
    max_overbooked_ratio: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Допустимая доля занятий, которые могут уйти в overbooking",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Теги услуги (например, beginner, evening, women_only)",
    )


class ServiceCreate(ServiceBase):
    """Создание услуги."""

    studio_id: int = Field(..., description="ID студии")


class ServiceUpdate(BaseModel):
    """Обновление услуги."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=1000)
    type: str | None = Field(None, description="Тип услуги")
    category: ServiceCategory | None = Field(
        None,
        description="Категория услуги",
    )
    duration_minutes: int | None = Field(None, ge=1)
    max_capacity: int | None = Field(None, ge=1)
    price_single_cents: int | None = Field(None, ge=0)
    price_course_cents: int | None = Field(None, ge=0)
    is_active: bool | None = None
    soft_limit_ratio: float | None = Field(
        None,
        ge=1.0,
        le=2.0,
        description="Соотношение soft‑лимита к max_capacity",
    )
    hard_limit_ratio: float | None = Field(
        None,
        ge=1.0,
        le=3.0,
        description="Соотношение hard‑лимита к max_capacity",
    )
    max_overbooked_ratio: float | None = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Допустимая доля занятий, которые могут уйти в overbooking",
    )
    tags: list[str] | None = Field(
        None,
        description="Теги услуги",
    )


class ServiceResponse(ServiceBase):
    """Ответ с услугой."""

    id: int
    studio_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScheduleBase(BaseModel):
    """Базовые поля расписания."""

    day_of_week: int = Field(..., ge=0, le=6, description="День недели 0-6 (Пн-Вс)")
    start_time: time = Field(..., description="Время начала занятия")
    valid_from: date = Field(..., description="Дата начала действия расписания")
    valid_to: date | None = Field(
        None,
        description="Дата окончания действия расписания (включительно)",
    )


class ScheduleCreate(ScheduleBase):
    """Создание расписания услуги."""

    service_id: int = Field(..., description="ID услуги")


class ScheduleResponse(ScheduleBase):
    """Ответ с расписанием."""

    id: int
    service_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Базовые поля заказа."""

    total_amount_cents: int = Field(..., ge=0, description="Сумма заказа в центах")
    currency: str = Field("eur", max_length=10, description="Валюта заказа")


class OrderResponse(OrderBase):
    """Ответ с заказом."""

    id: int
    studio_id: int
    service_id: int | None
    user_id: int | None
    guest_email: EmailStr | None
    guest_name: str | None
    status: str = Field(..., description="Статус заказа")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseBookingPreviewItem(BaseModel):
    """Информация о конкретном занятии в курсе при проверке доступности."""

    slot_id: int
    start_time: datetime
    max_capacity: int
    confirmed_count: int
    pending_count: int
    total_after_booking: int
    is_over_soft_limit: bool
    is_over_hard_limit: bool


class CourseAvailabilityResult(BaseModel):
    """
    Результат проверки доступности курса.

    Используется для фронтенда, чтобы показать предупреждения:
    - какие занятия будут "переполнены"
    - можно ли всё ещё покупать курс
    """

    can_book: bool = Field(..., description="Можно ли оформить курс")
    requires_warning: bool = Field(
        ...,
        description="Нужно ли показать пользователю предупреждение",
    )
    hard_block: bool = Field(
        ...,
        description="Заблокирована ли покупка из-за превышения hard‑лимита",
    )
    overbooked_slots: list[CourseBookingPreviewItem] = Field(
        default_factory=list,
        description="Список занятий, где произойдёт overbooking",
    )
    message: str | None = Field(
        None,
        description="Человеко‑читаемое сообщение для UI",
    )


class CourseBookingCreate(BaseModel):
    """
    Запрос на покупку курса.

    Вариант для гостя: без user_id, с email/именем.
    Вариант для аутентифицированного пользователя можно расширить позже.
    """

    service_id: int = Field(..., description="ID услуги‑курса")
    guest_name: str = Field(..., min_length=1, max_length=100)
    guest_email: EmailStr = Field(..., description="Email гостя")
    guest_phone: str | None = Field(None, max_length=20)


class CourseBookingResponse(BaseModel):
    """
    Ответ после успешного создания курсового заказа и букингов.

    Используется до интеграции со Stripe; позже можно добавить checkout_url.
    """

    order: OrderResponse
    bookings: list["BookingResponse"]
    availability: CourseAvailabilityResult | None = None


class ServiceAvailabilityScheduleItem(BaseModel):
    """Информация о конкретной дате курса для pre‑check."""

    date: date
    is_overbooked: bool
    remaining: int
    overbooking_status: str | None = Field(
        None,
        description="SOFT_LIMIT_REACHED / HARD_LIMIT_REACHED или None",
    )


class ServiceAvailabilityResponse(BaseModel):
    """
    Подробная информация о доступности курса для модалки покупки.
    """

    service_id: int
    can_book: bool
    requires_warning: bool
    warning_message: str | None
    schedule_details: list[ServiceAvailabilityScheduleItem]


class PublicServiceOccurrence(BaseModel):
    """Occurrence (слот) для публичного ответа студии."""

    id: int
    start_time: datetime
    is_full: bool


class PublicService(BaseModel):
    """
    Публичное описание услуги для карточки (полароид).

    Спроектировано под фронтовую витрину:
    - ближайший старт потока
    - количество занятий в потоке
    - агрегированная доступность
    """

    id: int
    name: str
    description: str | None
    type: str
    duration_minutes: int
    max_capacity: int
    price_single_cents: int
    price_course_cents: int | None
    cover_image_url: str | None = Field(
        None,
        description="URL обложки/фото класса (может настраиваться позже)",
    )
    next_term_start: datetime | None = Field(
        None,
        description="Дата и время ближайшего занятия текущего потока",
    )
    term_end: datetime | None = Field(
        None,
        description="Дата и время последнего занятия текущего потока",
    )
    occurrences_count: int = Field(
        0,
        description="Количество занятий в текущем (ближайшем) потоке",
    )

    class Availability(BaseModel):
        """Агрегированная доступность курса для карточки."""

        can_book: bool
        total_remaining_capacity: int
        requires_warning: bool
        overbooked_dates: list[date] = Field(
            default_factory=list,
            description="Даты занятий, где произойдёт overbooking",
        )

    availability: "PublicService.Availability | None" = Field(
        None,
        description="Информация о доступности для бронирования курса",
    )


class StudioPublicResponse(BaseModel):
    """Публичный ответ студии: основная инфа + список услуг."""

    id: int
    name: str
    slug: str | None
    description: str | None
    services: list[PublicService] = Field(default_factory=list)

