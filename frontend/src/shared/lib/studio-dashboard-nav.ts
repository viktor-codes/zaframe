import { StudioPermission } from "./constants";

export type StudioDashboardNavId =
  | "today"
  | "profile"
  | "services"
  | "calendar"
  | "bookings"
  | "team"
  | "payouts";

export interface StudioDashboardNavItem {
  id: StudioDashboardNavId;
  label: string;
  href: string;
  /** Exact match only (Today overview). */
  isExact?: boolean;
  /**
   * When set, item is shown only if the user has this permission.
   * Today has no permission — any studio member with dashboard access sees it.
   */
  permission?: StudioPermission;
}

/**
 * Full studio dashboard nav (before permission filtering).
 * STRATEGY §6: instructor sees Today + bookings; no services/schedule/profile/team/payouts.
 */
export function buildStudioDashboardNav(
  studioId: number,
): StudioDashboardNavItem[] {
  const base = `/dashboard/studios/${studioId}`;
  return [
    { id: "today", label: "Today", href: base, isExact: true },
    {
      id: "profile",
      label: "Profile",
      href: `${base}/profile`,
      permission: StudioPermission.MANAGE_STUDIO,
    },
    {
      id: "services",
      label: "Services",
      href: `${base}/services`,
      permission: StudioPermission.MANAGE_SERVICES,
    },
    {
      id: "calendar",
      label: "Calendar",
      href: `${base}/calendar`,
      permission: StudioPermission.MANAGE_SCHEDULE,
    },
    {
      id: "bookings",
      label: "Bookings",
      href: `${base}/bookings`,
      permission: StudioPermission.VIEW_BOOKINGS,
    },
    {
      id: "team",
      label: "Team",
      href: `${base}/team`,
      permission: StudioPermission.MANAGE_MEMBERS,
    },
    {
      id: "payouts",
      label: "Payouts",
      href: `${base}/payouts`,
      permission: StudioPermission.MANAGE_PAYOUTS,
    },
  ];
}

export function filterStudioDashboardNav(
  items: readonly StudioDashboardNavItem[],
  can: (permission: StudioPermission) => boolean,
): StudioDashboardNavItem[] {
  return items.filter(
    (item) => item.permission == null || can(item.permission),
  );
}
