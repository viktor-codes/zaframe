import {
  isStudioMemberRole,
  StudioMemberRole,
  UserRole,
} from "@shared/lib/constants";

import type { StudioRoleResponse, UserProfile } from "./types";

export function getUserDisplayName(user: Pick<UserProfile, "name" | "email">): string {
  const name = user.name.trim();
  return name.length > 0 ? name : user.email;
}

export function isGlobalStudioOwner(user: Pick<UserProfile, "role">): boolean {
  return user.role === UserRole.STUDIO_OWNER;
}

export function isGlobalAdmin(user: Pick<UserProfile, "role">): boolean {
  return user.role === UserRole.ADMIN;
}

export function getStudioRole(
  user: Pick<UserProfile, "roles">,
  studioId: number,
): StudioMemberRole | null {
  const membership = user.roles?.find((role) => role.studio_id === studioId);
  if (!membership || !isStudioMemberRole(membership.role)) {
    return null;
  }
  return membership.role;
}

/**
 * Check membership against an allow-list.
 * Prefer `@shared/auth` `hasStudioRole` / `usePermission` in UI gates.
 */
export function userHasStudioRole(
  user: Pick<UserProfile, "roles">,
  studioId: number,
  allowedRoles: readonly StudioMemberRole[],
): boolean {
  const role = getStudioRole(user, studioId);
  return role != null && allowedRoles.includes(role);
}

export function listStudioMemberships(
  user: Pick<UserProfile, "roles">,
): StudioRoleResponse[] {
  return user.roles ?? [];
}

export { StudioMemberRole, UserRole };
