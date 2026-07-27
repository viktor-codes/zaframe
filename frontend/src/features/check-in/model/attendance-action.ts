import { BookingStatus } from "@shared/lib";

import type { BookingOwnerResponse } from "@entities/booking";

type AttendanceInput = Pick<
  BookingOwnerResponse,
  "status" | "checked_in_at" | "no_show_at"
>;

/** True when staff can check the attendee in. */
export function canCheckIn(booking: AttendanceInput): boolean {
  if (booking.checked_in_at != null) return false;
  if (booking.no_show_at != null || booking.status === BookingStatus.NO_SHOW) {
    return false;
  }
  return booking.status === BookingStatus.CONFIRMED;
}

/** True when staff can still mark no-show (confirmed, not checked in). */
export function canMarkNoShow(booking: AttendanceInput): boolean {
  if (booking.checked_in_at != null) return false;
  if (booking.no_show_at != null || booking.status === BookingStatus.NO_SHOW) {
    return false;
  }
  return booking.status === BookingStatus.CONFIRMED;
}

/** Guest display name for a staff participant row. */
export function getParticipantDisplayName(
  booking: Pick<BookingOwnerResponse, "id" | "guest_name" | "guest_email">,
): string {
  const name = booking.guest_name?.trim();
  if (name) return name;
  const email = booking.guest_email?.trim();
  if (email) return email;
  return `Booking #${booking.id}`;
}
