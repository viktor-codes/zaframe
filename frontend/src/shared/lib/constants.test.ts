import { describe, expect, it } from "vitest";

import {
  BookingPaymentStatus,
  BookingStatus,
  BOOKING_ACTIVE_STATUSES,
  OrderStatus,
  OccurrenceStatus,
  roleHasPermission,
  ServiceVisibility,
  StudioMemberRole,
  StudioPermission,
  STUDIO_PERMISSIONS_BY_ROLE,
  UserRole,
} from "./constants";

describe("STUDIO_PERMISSIONS_BY_ROLE", () => {
  it("gives owner every permission", () => {
    for (const permission of Object.values(StudioPermission)) {
      expect(roleHasPermission(StudioMemberRole.OWNER, permission)).toBe(true);
    }
  });

  it("denies manage_studio and manage_members to manager", () => {
    expect(
      roleHasPermission(
        StudioMemberRole.MANAGER,
        StudioPermission.MANAGE_STUDIO,
      ),
    ).toBe(false);
    expect(
      roleHasPermission(
        StudioMemberRole.MANAGER,
        StudioPermission.MANAGE_MEMBERS,
      ),
    ).toBe(false);
    expect(
      roleHasPermission(
        StudioMemberRole.MANAGER,
        StudioPermission.MANAGE_SERVICES,
      ),
    ).toBe(true);
  });

  it("limits instructor to dashboard, view bookings, and check-in", () => {
    expect(STUDIO_PERMISSIONS_BY_ROLE[StudioMemberRole.INSTRUCTOR]).toEqual([
      StudioPermission.VIEW_DASHBOARD,
      StudioPermission.VIEW_BOOKINGS,
      StudioPermission.CHECK_IN_BOOKING,
    ]);
    expect(
      roleHasPermission(
        StudioMemberRole.INSTRUCTOR,
        StudioPermission.MANAGE_SCHEDULE,
      ),
    ).toBe(false);
  });

  it("returns false for unknown or empty roles", () => {
    expect(roleHasPermission(null, StudioPermission.VIEW_DASHBOARD)).toBe(
      false,
    );
    expect(roleHasPermission("admin", StudioPermission.VIEW_DASHBOARD)).toBe(
      false,
    );
  });
});

describe("status constants", () => {
  it("exposes booking statuses matching the backend lifecycle", () => {
    expect(Object.values(BookingStatus)).toEqual([
      "pending",
      "confirmed",
      "cancelled",
      "expired",
      "completed",
      "no_show",
    ]);
    expect(BOOKING_ACTIVE_STATUSES.includes(BookingStatus.PENDING)).toBe(true);
    expect(BOOKING_ACTIVE_STATUSES.includes(BookingStatus.CANCELLED)).toBe(
      false,
    );
  });

  it("exposes order, occurrence, and visibility enums", () => {
    expect(OrderStatus.MANUAL_REVIEW).toBe("manual_review");
    expect(OccurrenceStatus.SCHEDULED).toBe("scheduled");
    expect(ServiceVisibility.PUBLISHED).toBe("published");
    expect(UserRole.STUDIO_OWNER).toBe("studio_owner");
  });

  it("exposes booking payment statuses used by the webhook pipeline", () => {
    expect(BookingPaymentStatus.SUCCEEDED).toBe("succeeded");
    expect(BookingPaymentStatus.OVERBOOKED_MANUAL_REVIEW).toBe(
      "overbooked_manual_review",
    );
  });
});
