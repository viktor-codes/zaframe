import type { StudioRoleResponse, UserProfile } from "./types";

export const GLOBAL_USER_ROLE = {
  USER: "user",
  STUDIO_OWNER: "studio_owner",
  ADMIN: "admin",
} as const;

export const STUDIO_MEMBER_ROLE = {
  OWNER: "owner",
  MANAGER: "manager",
  INSTRUCTOR: "instructor",
} as const;

export function getUserDisplayName(user: Pick<UserProfile, "name" | "email">): string {
  const name = user.name.trim();
  return name.length > 0 ? name : user.email;
}

export function isGlobalStudioOwner(user: Pick<UserProfile, "role">): boolean {
  return user.role === GLOBAL_USER_ROLE.STUDIO_OWNER;
}

export function isGlobalAdmin(user: Pick<UserProfile, "role">): boolean {
  return user.role === GLOBAL_USER_ROLE.ADMIN;
}

export function getStudioRole(
  user: Pick<UserProfile, "roles">,
  studioId: number,
): string | null {
  const membership = user.roles?.find((role) => role.studio_id === studioId);
  return membership?.role ?? null;
}

export function hasStudioRole(
  user: Pick<UserProfile, "roles">,
  studioId: number,
  allowedRoles: readonly string[],
): boolean {
  const role = getStudioRole(user, studioId);
  return role != null && allowedRoles.includes(role);
}

export function listStudioMemberships(
  user: Pick<UserProfile, "roles">,
): StudioRoleResponse[] {
  return user.roles ?? [];
}
