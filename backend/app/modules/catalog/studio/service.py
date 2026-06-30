"""
Business logic for studios.

Why the service layer exists:
- Routers stay thin and handle only HTTP concerns
- Business logic lives in one place and is easier to test
- Logic can be reused across endpoints, webhooks, and CLI scripts
"""

from typing import Literal

import structlog

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.models.studio_member import StudioMember, StudioMemberRole
from app.models.user import User, UserRole
from app.modules.catalog.studio.schemas import StudioCreate, StudioRoleResponse, StudioUpdate

StudioPermission = Literal[
    "view_dashboard",
    "manage_studio",
    "manage_services",
    "manage_schedule",
    "view_bookings",
    "manage_bookings",
    "check_in_booking",
    "manage_payouts",
    "manage_members",
]
logger = structlog.get_logger(__name__)

STUDIO_PERMISSIONS_BY_ROLE: dict[str, frozenset[StudioPermission]] = {
    StudioMemberRole.OWNER.value: frozenset(
        {
            "view_dashboard",
            "manage_studio",
            "manage_services",
            "manage_schedule",
            "view_bookings",
            "manage_bookings",
            "check_in_booking",
            "manage_payouts",
            "manage_members",
        }
    ),
    StudioMemberRole.MANAGER.value: frozenset(
        {
            "view_dashboard",
            "manage_services",
            "manage_schedule",
            "view_bookings",
            "manage_bookings",
            "check_in_booking",
            "manage_payouts",
        }
    ),
    StudioMemberRole.INSTRUCTOR.value: frozenset(
        {
            "view_dashboard",
            "view_bookings",
            "check_in_booking",
        }
    ),
}


async def get_studio(uow: UnitOfWork, studio_id: int) -> Studio | None:
    """Get a studio by ID, returning None when missing."""
    return await uow.studios.get_by_id(studio_id)


async def get_studios(
    uow: UnitOfWork,
    *,
    skip: int = 0,
    limit: int = 20,
    owner_id: int | None = None,
    is_active: bool | None = None,
    city: str | None = None,
    category: str | None = None,
    query: str | None = None,
    amenities: list[str] | None = None,
) -> list[Studio]:
    """List studios with pagination and filters."""
    return await uow.studios.list_(
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category,
        query=query,
        amenities=amenities,
    )


async def get_studios_count(
    uow: UnitOfWork,
    *,
    owner_id: int | None = None,
    is_active: bool | None = None,
    city: str | None = None,
    category: str | None = None,
    query: str | None = None,
    amenities: list[str] | None = None,
) -> int:
    """Count studios for pagination using the same filters as get_studios."""
    return await uow.studios.count(
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category,
        query=query,
        amenities=amenities,
    )


async def get_my_studios(uow: UnitOfWork, *, user_id: int) -> list[StudioMember]:
    """List studio memberships for the current user."""
    return await uow.studio_members.list_for_user(user_id=user_id)


async def get_current_user_studio_roles(
    uow: UnitOfWork,
    *,
    user_id: int,
) -> list[StudioRoleResponse]:
    """Return studio-scoped roles for navigation and client-side hints."""
    memberships = await uow.studio_members.list_for_user(user_id=user_id)
    return [
        StudioRoleResponse(studio_id=membership.studio_id, role=membership.role)
        for membership in memberships
    ]


async def get_studio_or_raise(uow: UnitOfWork, studio_id: int) -> Studio:
    """Get a studio by ID or raise NotFoundError."""
    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Studio not found")
    return studio


def ensure_studio_owner(studio: Studio, user_id: int) -> None:
    """Legacy owner_id check kept for compatibility with older call sites."""
    if studio.owner_id != user_id:
        raise ForbiddenError("Access denied for this studio")


async def _get_studio_role(
    uow: UnitOfWork,
    *,
    studio: Studio,
    user: User,
) -> str | None:
    membership = await uow.studio_members.get_by_studio_and_user(
        studio_id=studio.id,
        user_id=user.id,
    )
    if membership is not None:
        return membership.role
    if studio.owner_id == user.id:
        return StudioMemberRole.OWNER.value
    return None


async def has_studio_permission(
    uow: UnitOfWork,
    *,
    studio: Studio,
    user: User,
    permission: StudioPermission,
    allow_admin_bypass: bool = False,
) -> bool:
    """Check a studio-scoped permission without raising."""
    if allow_admin_bypass and user.role == UserRole.ADMIN.value:
        return True
    role = await _get_studio_role(uow, studio=studio, user=user)
    if role is None:
        return False
    return permission in STUDIO_PERMISSIONS_BY_ROLE.get(role, frozenset())


async def require_studio_permission(
    uow: UnitOfWork,
    *,
    studio: Studio,
    user: User,
    permission: StudioPermission,
    allow_admin_bypass: bool = False,
) -> None:
    """Raise ForbiddenError unless the user has the requested studio permission."""
    if not await has_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission=permission,
        allow_admin_bypass=allow_admin_bypass,
    ):
        log_domain_event(
            logger,
            "permission_denied",
            level="warning",
            user_id=user.id,
            studio_id=studio.id,
            permission=permission,
        )
        raise ForbiddenError("Access denied for this studio")


async def ensure_studio_slug_available(
    uow: UnitOfWork,
    *,
    slug: str | None,
    current_studio_id: int | None = None,
) -> None:
    """Validate slug uniqueness across studios."""
    if slug is None:
        return
    existing = await uow.studios.get_by_slug(slug)
    if existing is not None and existing.id != current_studio_id:
        raise ConflictError("Studio slug is already in use")


async def create_studio(uow: UnitOfWork, schema: StudioCreate) -> Studio:
    """Create a studio; owner_id must be set from the router-level token."""
    if schema.owner_id is None:
        raise ValidationError("Owner is missing or not found")
    owner = await uow.users.get_by_id(schema.owner_id)
    if owner is None:
        raise ValidationError("Owner is missing or not found")
    await ensure_studio_slug_available(uow, slug=schema.slug)

    studio = Studio(
        owner_id=schema.owner_id,
        name=schema.name,
        slug=schema.slug,
        description=schema.description,
        logo_url=schema.logo_url,
        cover_url=schema.cover_url,
        email=schema.email,
        phone=schema.phone,
        address=schema.address,
        city=schema.city,
        latitude=schema.latitude,
        longitude=schema.longitude,
        amenities=schema.amenities,
        timezone=schema.timezone,
        cancel_before_hours=schema.cancel_before_hours,
    )
    studio = await uow.studios.add(studio)
    await uow.studio_members.add(
        StudioMember(
            studio_id=studio.id,
            user_id=schema.owner_id,
            role=StudioMemberRole.OWNER.value,
        )
    )
    log_domain_event(
        logger,
        "studio_member_added",
        studio_id=studio.id,
        user_id=schema.owner_id,
        role=StudioMemberRole.OWNER.value,
    )
    if owner.role == UserRole.USER.value:
        owner.role = UserRole.STUDIO_OWNER.value
        await uow.users.save(owner)
    log_domain_event(logger, "studio_created", studio_id=studio.id, user_id=schema.owner_id)
    return studio


async def update_studio(
    uow: UnitOfWork,
    studio: Studio,
    schema: StudioUpdate,
) -> Studio:
    """Partially update a studio."""
    update_data = schema.model_dump(exclude_unset=True)
    if "timezone" in update_data and update_data["timezone"] != studio.timezone:
        occurrence_count = await uow.occurrences.count(studio_id=studio.id)
        if occurrence_count > 0:
            raise ValidationError("Cannot change timezone after occurrences have been created")
    if "slug" in update_data:
        await ensure_studio_slug_available(
            uow,
            slug=update_data["slug"],
            current_studio_id=studio.id,
        )
    for field, value in update_data.items():
        setattr(studio, field, value)
    updated_studio = await uow.studios.save(studio)
    log_domain_event(
        logger,
        "studio_updated",
        studio_id=updated_studio.id,
        updated_fields=sorted(update_data.keys()),
    )
    return updated_studio


async def delete_studio(uow: UnitOfWork, studio: Studio) -> None:
    """Delete studio. Cascades to related occurrences."""
    await uow.studios.delete(studio)
