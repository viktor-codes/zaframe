"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field

from app.schemas.user import UserResponse


class OTPRequest(BaseModel):
    """Request an email OTP code."""

    email: EmailStr = Field(..., description="Email for sign-in")
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name (used only when creating a new account)",
    )


class OTPVerify(BaseModel):
    """Verify email OTP and start a session."""

    email: EmailStr = Field(..., description="Email the code was sent to")
    code: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit code from email",
    )
    booking_id: int | None = Field(
        None,
        description="Optional pending booking to attach to the user after verify",
    )


class TokenResponse(BaseModel):
    """Access token response.

    Refresh token is stored in an httpOnly cookie (strict mode) and is not
    returned in the JSON body.
    """

    access_token: str = Field(..., description="API access token")
    token_type: str = Field(default="bearer", description="Token type")


class OTPSentResponse(BaseModel):
    """Response after requesting an OTP email."""

    message: str = Field(
        default="If the email is valid, you will receive a verification code",
        description="User-facing message",
    )


class OTPVerifyResponse(TokenResponse):
    """OTP verify response with current user profile."""

    user: UserResponse = Field(..., description="Authenticated user")
