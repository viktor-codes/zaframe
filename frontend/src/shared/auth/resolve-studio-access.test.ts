import { describe, expect, it } from "vitest";

import { StudioMemberRole, StudioPermission } from "@shared/lib/constants";

import {
  canStudioPermission,
  hasStudioRole,
  resolveStudioRole,
} from "./resolve-studio-access";
import type { AuthUser } from "./types";

function userWithRoles(roles: { studio_id: number; role: string }[]): AuthUser {
  return {
    id: 1,
    email: "a@b.c",
    roles,
  } as AuthUser;
}

describe("resolveStudioRole", () => {
  it("returns the role for the matching studio", () => {
    const user = userWithRoles([
      { studio_id: 1, role: "owner" },
      { studio_id: 2, role: "instructor" },
    ]);
    expect(resolveStudioRole(user, 2)).toBe(StudioMemberRole.INSTRUCTOR);
  });

  it("returns null when missing or unknown role string", () => {
    expect(resolveStudioRole(null, 1)).toBeNull();
    expect(resolveStudioRole(userWithRoles([]), 1)).toBeNull();
    expect(
      resolveStudioRole(userWithRoles([{ studio_id: 1, role: "admin" }]), 1),
    ).toBeNull();
  });
});

describe("canStudioPermission / hasStudioRole", () => {
  const owner = userWithRoles([{ studio_id: 10, role: "owner" }]);
  const instructor = userWithRoles([{ studio_id: 10, role: "instructor" }]);

  it("checks permissions via the shared matrix", () => {
    expect(canStudioPermission(owner, 10, StudioPermission.MANAGE_STUDIO)).toBe(
      true,
    );
    expect(
      canStudioPermission(instructor, 10, StudioPermission.MANAGE_STUDIO),
    ).toBe(false);
    expect(
      canStudioPermission(instructor, 10, StudioPermission.CHECK_IN_BOOKING),
    ).toBe(true);
  });

  it("checks allowed role lists", () => {
    expect(hasStudioRole(instructor, 10)).toBe(true);
    expect(
      hasStudioRole(instructor, 10, [
        StudioMemberRole.OWNER,
        StudioMemberRole.MANAGER,
      ]),
    ).toBe(false);
    expect(hasStudioRole(owner, 10, [StudioMemberRole.OWNER])).toBe(true);
  });
});
