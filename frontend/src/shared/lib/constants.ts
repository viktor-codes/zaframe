/**
 * Domain statuses, roles, and studio permissions — single source of truth for the UI.
 *
 * WHY: never compare raw status/permission strings in components. Keep this matrix in
 * sync with `backend/app/modules/catalog/studio/service.py` (`STUDIO_PERMISSIONS_BY_ROLE`)
 * and entity status classes under `backend/app/models/`. See CONTRACTS.md §2–3.
 *
 * Arrays (not Set) so values survive JSON / RSC→client serialization.
 */

// ── Global user roles ───────────────────────────────────────────────────────

export const UserRole = {
  USER: "user",
  STUDIO_OWNER: "studio_owner",
  ADMIN: "admin",
} as const;

export type UserRole = (typeof UserRole)[keyof typeof UserRole];

// ── Studio member roles ─────────────────────────────────────────────────────

export const StudioMemberRole = {
  OWNER: "owner",
  MANAGER: "manager",
  INSTRUCTOR: "instructor",
} as const;

export type StudioMemberRole =
  (typeof StudioMemberRole)[keyof typeof StudioMemberRole];

// ── Studio permissions ──────────────────────────────────────────────────────

export const StudioPermission = {
  VIEW_DASHBOARD: "view_dashboard",
  MANAGE_STUDIO: "manage_studio",
  MANAGE_SERVICES: "manage_services",
  MANAGE_SCHEDULE: "manage_schedule",
  VIEW_BOOKINGS: "view_bookings",
  MANAGE_BOOKINGS: "manage_bookings",
  CHECK_IN_BOOKING: "check_in_booking",
  MANAGE_PAYOUTS: "manage_payouts",
  MANAGE_MEMBERS: "manage_members",
} as const;

export type StudioPermission =
  (typeof StudioPermission)[keyof typeof StudioPermission];

/**
 * Mirror of backend `STUDIO_PERMISSIONS_BY_ROLE`.
 * Frontend gates are UX-only; the API enforces permissions server-side.
 */
export const STUDIO_PERMISSIONS_BY_ROLE: Record<
  StudioMemberRole,
  readonly StudioPermission[]
> = {
  [StudioMemberRole.OWNER]: [
    StudioPermission.VIEW_DASHBOARD,
    StudioPermission.MANAGE_STUDIO,
    StudioPermission.MANAGE_SERVICES,
    StudioPermission.MANAGE_SCHEDULE,
    StudioPermission.VIEW_BOOKINGS,
    StudioPermission.MANAGE_BOOKINGS,
    StudioPermission.CHECK_IN_BOOKING,
    StudioPermission.MANAGE_PAYOUTS,
    StudioPermission.MANAGE_MEMBERS,
  ],
  [StudioMemberRole.MANAGER]: [
    StudioPermission.VIEW_DASHBOARD,
    StudioPermission.MANAGE_SERVICES,
    StudioPermission.MANAGE_SCHEDULE,
    StudioPermission.VIEW_BOOKINGS,
    StudioPermission.MANAGE_BOOKINGS,
    StudioPermission.CHECK_IN_BOOKING,
    StudioPermission.MANAGE_PAYOUTS,
  ],
  [StudioMemberRole.INSTRUCTOR]: [
    StudioPermission.VIEW_DASHBOARD,
    StudioPermission.VIEW_BOOKINGS,
    StudioPermission.CHECK_IN_BOOKING,
  ],
};

export function isStudioMemberRole(value: string): value is StudioMemberRole {
  return (
    value === StudioMemberRole.OWNER ||
    value === StudioMemberRole.MANAGER ||
    value === StudioMemberRole.INSTRUCTOR
  );
}

export function roleHasPermission(
  role: string | null | undefined,
  permission: StudioPermission,
): boolean {
  if (!role || !isStudioMemberRole(role)) return false;
  return STUDIO_PERMISSIONS_BY_ROLE[role].includes(permission);
}

// ── Booking ─────────────────────────────────────────────────────────────────

export const BookingStatus = {
  PENDING: "pending",
  CONFIRMED: "confirmed",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
  COMPLETED: "completed",
  NO_SHOW: "no_show",
} as const;

export type BookingStatus = (typeof BookingStatus)[keyof typeof BookingStatus];

/** Statuses that still hold a seat on an occurrence (backend ACTIVE_STATUSES). */
export const BOOKING_ACTIVE_STATUSES: readonly BookingStatus[] = [
  BookingStatus.PENDING,
  BookingStatus.CONFIRMED,
];

export const BookingType = {
  SINGLE: "single",
  COURSE: "course",
} as const;

export type BookingType = (typeof BookingType)[keyof typeof BookingType];

/**
 * Values written to `booking.payment_status` by the payment / webhook pipeline.
 * Distinct from ledger `PaymentStatus` filters and from `OrderStatus`.
 */
export const BookingPaymentStatus = {
  PENDING: "pending",
  UNPAID: "unpaid",
  SUCCEEDED: "succeeded",
  FAILED: "failed",
  REFUNDED: "refunded",
  PARTIALLY_REFUNDED: "partially_refunded",
  MANUAL_REVIEW: "manual_review",
  OVERBOOKED_MANUAL_REVIEW: "overbooked_manual_review",
} as const;

export type BookingPaymentStatus =
  (typeof BookingPaymentStatus)[keyof typeof BookingPaymentStatus];

// ── Order ───────────────────────────────────────────────────────────────────

export const OrderStatus = {
  PENDING: "pending",
  PAID: "paid",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
  REFUNDED: "refunded",
  MANUAL_REVIEW: "manual_review",
} as const;

export type OrderStatus = (typeof OrderStatus)[keyof typeof OrderStatus];

// ── Occurrence ──────────────────────────────────────────────────────────────

export const OccurrenceStatus = {
  SCHEDULED: "scheduled",
  CANCELLED: "cancelled",
  COMPLETED: "completed",
} as const;

export type OccurrenceStatus =
  (typeof OccurrenceStatus)[keyof typeof OccurrenceStatus];

// ── Service visibility ──────────────────────────────────────────────────────

export const ServiceVisibility = {
  DRAFT: "draft",
  PUBLISHED: "published",
  ARCHIVED: "archived",
} as const;

export type ServiceVisibility =
  (typeof ServiceVisibility)[keyof typeof ServiceVisibility];
