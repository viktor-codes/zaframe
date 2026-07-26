import type { BookingLike } from "./types";
import {
  BookingPaymentStatus,
  BookingStatus,
} from "@shared/lib/constants";

type BookingState = Pick<
  BookingLike,
  "status" | "reserved_until" | "is_guest_booking" | "cancelled_at"
>;

type BookingPaymentState = {
  status: string;
  payment_status?: string | null;
};

export function isPendingBooking(booking: Pick<BookingState, "status">): boolean {
  return booking.status === BookingStatus.PENDING;
}

export function isConfirmedBooking(
  booking: Pick<BookingState, "status">,
): boolean {
  return booking.status === BookingStatus.CONFIRMED;
}

/** True when webhook (or free confirm) marked payment complete on the booking. */
export function isBookingPaymentSucceeded(
  booking: Pick<BookingPaymentState, "payment_status">,
): boolean {
  return booking.payment_status === BookingPaymentStatus.SUCCEEDED;
}

/**
 * Pending unpaid hold that still needs Stripe Checkout.
 * Free sessions (`price_cents === 0`) never need checkout.
 */
export function bookingNeedsCheckoutPayment(
  booking: BookingPaymentState,
  occurrence: { price_cents: number },
): boolean {
  if (occurrence.price_cents <= 0) return false;
  if (isConfirmedBooking(booking)) return false;
  if (isBookingPaymentSucceeded(booking)) return false;
  return isPendingBooking(booking);
}

/**
 * True when the guest can still open Stripe Checkout for this hold.
 * Expired `reserved_until` means the seat was released — Pay must be disabled.
 */
export function canCompleteBookingPayment(
  booking: BookingPaymentState & { reserved_until?: string | null },
  occurrence: { price_cents: number },
  now: Date = new Date(),
): boolean {
  if (!bookingNeedsCheckoutPayment(booking, occurrence)) return false;
  return !isBookingReservationExpired(booking, now);
}

export function isCancelledBooking(
  booking: Pick<BookingState, "status" | "cancelled_at">,
): boolean {
  return (
    booking.status === BookingStatus.CANCELLED || booking.cancelled_at != null
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
    booking.status !== BookingStatus.CONFIRMED &&
    booking.status !== BookingStatus.PENDING
  ) {
    return false;
  }

  const occurrenceStartMs = new Date(occurrence.start_time).getTime();
  const cutoffMs = studio.cancel_before_hours * 60 * 60 * 1000;

  return occurrenceStartMs - now.getTime() >= cutoffMs;
}
