import { describe, expect, it } from "vitest";

import {
  roleHasPermission,
  StudioMemberRole,
  StudioPermission,
} from "./constants";
import {
  buildStudioDashboardNav,
  filterStudioDashboardNav,
} from "./studio-dashboard-nav";

describe("studio dashboard nav", () => {
  it("builds the full nav for a studio id", () => {
    const items = buildStudioDashboardNav(7);
    expect(items.map((item) => item.id)).toEqual([
      "today",
      "profile",
      "services",
      "calendar",
      "bookings",
      "payouts",
    ]);
    expect(items[0].href).toBe("/dashboard/studios/7");
    expect(items[0].isExact).toBe(true);
  });

  it("keeps Today + Bookings for instructors", () => {
    const can = (permission: StudioPermission) =>
      roleHasPermission(StudioMemberRole.INSTRUCTOR, permission);
    const visible = filterStudioDashboardNav(buildStudioDashboardNav(3), can);

    expect(visible.map((item) => item.id)).toEqual(["today", "bookings"]);
  });

  it("hides Profile for managers (no manage_studio)", () => {
    const can = (permission: StudioPermission) =>
      roleHasPermission(StudioMemberRole.MANAGER, permission);
    const visible = filterStudioDashboardNav(buildStudioDashboardNav(3), can);

    expect(visible.map((item) => item.id)).toEqual([
      "today",
      "services",
      "calendar",
      "bookings",
      "payouts",
    ]);
  });

  it("shows the full menu for owners", () => {
    const can = (permission: StudioPermission) =>
      roleHasPermission(StudioMemberRole.OWNER, permission);
    const visible = filterStudioDashboardNav(buildStudioDashboardNav(3), can);

    expect(visible.map((item) => item.id)).toEqual([
      "today",
      "profile",
      "services",
      "calendar",
      "bookings",
      "payouts",
    ]);
  });
});
