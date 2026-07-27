"""Studio CRUD and list use-cases. Permission helpers re-exported from permissions."""

import structlog

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.models.studio_member import StudioMember, StudioMemberRole
from app.models.user import UserRole
from app.modules.catalog.studio.permissions import (
    STUDIO_PERMISSIONS_BY_ROLE,
    StudioPermission,
    ensure_studio_owner,
    has_studio_permission,
    require_studio_permission,
)
from app.modules.catalog.studio.schemas import StudioCreate, StudioRoleResponse, StudioUpdate

__all__ = [
    "STUDIO_PERMISSIONS_BY_ROLE", "StudioPermission", "create_studio", "delete_studio",
    "ensure_studio_owner", "ensure_studio_slug_available", "get_current_user_studio_roles",
    "get_my_studios", "get_studio", "get_studio_or_raise", "get_studios", "get_studios_count",
    "has_studio_permission", "require_studio_permission", "update_studio",
]
logger = structlog.get_logger(__name__)


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
