"""Pydantic schemas for studio member management."""

from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, EmailStr, Field

AssignableStudioMemberRole = Literal["manager", "instructor"]


class StudioMemberCreate(BaseModel):
    """Add an existing user to a studio by email (no pending-invite flow in MVP)."""

    email: EmailStr = Field(
        ...,
        description="Email of an existing ZeeFrame user",
        examples=["instructor@example.com"],
    )
    role: AssignableStudioMemberRole = Field(
        ...,
        description="Assignable role; owner is created only with the studio",
        examples=["instructor"],
    )


class StudioMemberUpdate(BaseModel):
    """Change a member's role (owner demotion blocked when they are the last owner)."""

    role: AssignableStudioMemberRole = Field(
        ...,
        description="New role; owner cannot be assigned via this endpoint",
        examples=["manager"],
    )


class StudioMemberResponse(BaseModel):
    """Studio membership with nested user summary for the team UI."""

    id: int = Field(..., description="Studio member ID")
    studio_id: int = Field(..., description="Studio ID")
    user_id: int = Field(..., description="User ID")
    role: str = Field(..., description="Membership role: owner | manager | instructor")
    email: EmailStr = Field(..., description="Member email")
    name: str | None = Field(None, description="Member display name")
    created_at: AwareDatetime
    updated_at: AwareDatetime

    model_config = ConfigDict(from_attributes=True)
