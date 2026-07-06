import type { BookingLike } from "./types";

export const BOOKING_STATUS = {
  PENDING: "pending",
  CONFIRMED: "confirmed",
  COMPLETED: "completed",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
  NO_SHOW: "no_show",
} as const;

type BookingState = Pick<
  BookingLike,
  "status" | "reserved_until" | "is_guest_booking" | "cancelled_at"
>;

export function isPendingBooking(booking: Pick<BookingState, "status">): boolean {
  return booking.status === BOOKING_STATUS.PENDING;
}

export function isConfirmedBooking(
  booking: Pick<BookingState, "status">,
): boolean {
  return booking.status === BOOKING_STATUS.CONFIRMED;
}

export function isCancelledBooking(
  booking: Pick<BookingState, "status" | "cancelled_at">,
): boolean {
  return (
    booking.status === BOOKING_STATUS.CANCELLED || booking.cancelled_at != null
  );
}

export function isGuestBooking(
  booking: Pick<BookingState, "is_guest_booking">,
): boolean {
  return booking.is_guest_booking;
}

export function getBookingReservedUntilDate(
  booking: Pick<BookingState, "reserved_until">,
): Date | null {
  if (!booking.reserved_until) {
    return null;
  }

  return new Date(booking.reserved_until);
}

export function isBookingReservationExpired(
  booking: Pick<BookingState, "reserved_until" | "status">,
  now: Date = new Date(),
): boolean {
  if (!isPendingBooking(booking)) {
    return false;
  }

  const reservedUntil = getBookingReservedUntilDate(booking);
  if (!reservedUntil) {
    return false;
  }

  return reservedUntil.getTime() <= now.getTime();
}

export function getBookingReservationRemainingMs(
  booking: Pick<BookingState, "reserved_until" | "status">,
  now: Date = new Date(),
): number | null {
  if (!isPendingBooking(booking)) {
    return null;
  }

  const reservedUntil = getBookingReservedUntilDate(booking);
  if (!reservedUntil) {
    return null;
  }

  return Math.max(reservedUntil.getTime() - now.getTime(), 0);
}

export function canCustomerCancelBooking(
  booking: Pick<BookingState, "status" | "cancelled_at">,
  occurrence: { start_time: string },
  studio: { cancel_before_hours: number },
  now: Date = new Date(),
): boolean {
  if (isCancelledBooking(booking)) {
    return false;
  }

  if (
    booking.status !== BOOKING_STATUS.CONFIRMED &&
    booking.status !== BOOKING_STATUS.PENDING
  ) {
    return false;
  }

  const occurrenceStartMs = new Date(occurrence.start_time).getTime();
  const cutoffMs = studio.cancel_before_hours * 60 * 60 * 1000;

  return occurrenceStartMs - now.getTime() >= cutoffMs;
}
