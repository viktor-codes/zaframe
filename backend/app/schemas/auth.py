"""Pydantic schemas for authentication."""

from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """Magic link request payload."""

    email: EmailStr = Field(..., description="Email for sign-in")
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display name (for registration)",
    )


class TokenResponse(BaseModel):
    """Access token response.

    Refresh token is stored in an httpOnly cookie (strict mode) and is not
    returned in the JSON body.
    """

    access_token: str = Field(..., description="API access token")
    token_type: str = Field(default="bearer", description="Token type")


class MagicLinkSentResponse(BaseModel):
    """Response after requesting a magic link."""

    message: str = Field(
        default="If the email is registered, you will receive a sign-in link",
        description="User-facing message",
    )
