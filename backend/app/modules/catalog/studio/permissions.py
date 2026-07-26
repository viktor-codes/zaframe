"""Studio-scoped RBAC permissions and membership helpers."""

from typing import Literal

import structlog

from app.core.exceptions import ForbiddenError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.models.studio_member import StudioMemberRole
from app.models.user import User, UserRole

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
