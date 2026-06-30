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
