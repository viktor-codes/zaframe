/**
 * Pure helpers for studio role / permission checks (testable without React).
 */

import {
  isStudioMemberRole,
  roleHasPermission,
  type StudioMemberRole,
  type StudioPermission,
} from "@shared/lib/constants";

import type { AuthUser } from "./types";

/**
 * Resolve the current user's role in a studio from `/auth/me` roles[].
 */
export function resolveStudioRole(
  user: AuthUser | null | undefined,
  studioId: number | null | undefined,
): StudioMemberRole | null {
  if (!user || studioId == null) return null;
  const entry = user.roles?.find((item) => item.studio_id === studioId);
  if (!entry || !isStudioMemberRole(entry.role)) return null;
  return entry.role;
}

export function canStudioPermission(
  user: AuthUser | null | undefined,
  studioId: number | null | undefined,
  permission: StudioPermission,
): boolean {
  return roleHasPermission(resolveStudioRole(user, studioId), permission);
}

export function hasStudioRole(
  user: AuthUser | null | undefined,
  studioId: number | null | undefined,
  allowedRoles?: readonly StudioMemberRole[],
): boolean {
  const role = resolveStudioRole(user, studioId);
  if (!role) return false;
  if (!allowedRoles || allowedRoles.length === 0) return true;
  return allowedRoles.includes(role);
}
