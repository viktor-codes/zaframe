"""
Pydantic schemas for the User model.

RORO pattern (Receive an Object, Return an Object):
- UserCreate: data for creating a user
- UserUpdate: data for updating a user, all fields optional
- UserResponse: API response data including id and timestamps

Why separate schemas:
- Security: internal authentication fields are not returned
- Validation: create and update have different rules
- Flexibility: response schemas can add computed fields later
"""

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user fields shared by create and update schemas."""

    email: EmailStr = Field(..., description="Unique user email")
    name: str = Field(..., min_length=1, max_length=100, description="User name")
    phone: str | None = Field(None, max_length=20, description="Optional phone number")


class UserCreate(UserBase):
    """Schema for creating a user."""

    marketing_consent: bool = Field(
        default=False,
        description="Whether the user explicitly agreed to marketing communications",
    )


class UserUpdate(BaseModel):
    """Schema for updating a user; all fields are optional."""

    email: EmailStr | None = Field(None, description="User email")
    name: str | None = Field(None, min_length=1, max_length=100, description="User name")
    phone: str | None = Field(None, max_length=20, description="Phone number")
    marketing_consent: bool | None = Field(
        None,
        description="Whether the user agreed to marketing communications",
    )


class CurrentUserUpdate(BaseModel):
    """Editable current-user profile fields."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="User display name",
        examples=["Ada Lovelace"],
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="Optional phone number",
        examples=["+353871234567"],
    )
    marketing_consent: bool | None = Field(
        None,
        description="Whether the user agreed to marketing communications",
        examples=[False],
    )

    model_config = ConfigDict(extra="forbid")


class UserResponse(UserBase):
    """API response schema including id and timestamps."""

    id: int
    role: str
    is_active: bool
    marketing_consent: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime
    last_login_at: AwareDatetime | None
    deleted_at: AwareDatetime | None = Field(
        None,
        description="Soft-delete timestamp; null for active users",
    )

    model_config = ConfigDict(
        from_attributes=True,
    )  # Pydantic v2: allow creation from SQLAlchemy models


class UserPublic(UserBase):
    """Public user information without internal fields."""

    id: int
    created_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class UserExportItem(BaseModel):
    """User snapshot for GDPR data export (DSAR)."""

    id: int = Field(..., description="User id")
    email: EmailStr = Field(..., description="Account email")
    name: str | None = Field(None, description="Display name")
    phone: str | None = Field(None, description="Phone if set")
    marketing_consent: bool = Field(..., description="Marketing preference")
    created_at: AwareDatetime
    updated_at: AwareDatetime
    deleted_at: AwareDatetime | None = Field(
        None,
        description="Soft-delete timestamp; null while account is active",
    )

    model_config = ConfigDict(from_attributes=True)


class BookingExportItem(BaseModel):
    """Booking row included in a DSAR export (no Stripe secrets)."""

    id: int
    occurrence_id: int
    user_id: int | None = None
    status: str
    guest_name: str | None = None
    guest_email: str | None = None
    guest_phone: str | None = None
    payment_status: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    cancelled_at: AwareDatetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OrderExportItem(BaseModel):
    """Order row included in a DSAR export."""

    id: int
    studio_id: int
    service_id: int | None = None
    user_id: int | None = None
    guest_email: str | None = None
    guest_name: str | None = None
    guest_phone: str | None = None
    status: str
    total_amount_cents: int
    currency: str
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


class PaymentExportItem(BaseModel):
    """Payment ledger row for DSAR (Stripe ids are user-facing refs, not secrets)."""

    id: int
    booking_id: int | None = None
    order_id: int | None = None
    amount_cents: int
    currency: str
    status: str
    provider: str
    stripe_checkout_session_id: str
    paid_at: AwareDatetime | None = None
    refunded_amount_cents: int
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)


def _empty_booking_export_items() -> list[BookingExportItem]:
    return []


def _empty_order_export_items() -> list[OrderExportItem]:
    return []


def _empty_payment_export_items() -> list[PaymentExportItem]:
    return []


class UserDataExportResponse(BaseModel):
    """GDPR data export envelope for the authenticated user."""

    user: UserExportItem = Field(..., description="Account profile snapshot")
    bookings: list[BookingExportItem] = Field(
        default_factory=_empty_booking_export_items,
        description="Bookings linked by user_id or guest email",
    )
    orders: list[OrderExportItem] = Field(
        default_factory=_empty_order_export_items,
        description="Course orders linked by user_id or guest email",
    )
    payments: list[PaymentExportItem] = Field(
        default_factory=_empty_payment_export_items,
        description="Payment ledger rows for those bookings/orders",
    )

