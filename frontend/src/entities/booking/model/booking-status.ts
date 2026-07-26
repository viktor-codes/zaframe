import {
  BookingPaymentStatus,
  BookingStatus,
} from "@shared/lib/constants";
import { isBookingReservationExpired, isPendingBooking } from "./booking";

export type BookingStatusTone =
  | "neutral"
  | "amber"
  | "green"
  | "red"
  | "teal";

export interface BookingStatusPresentation {
  label: string;
  tone: BookingStatusTone;
}

type BookingStatusInput = {
  status: string;
  payment_status?: string | null;
  reserved_until?: string | null;
};

/**
 * Customer-facing label + tone for a booking status badge.
 * Prefers booking lifecycle over payment ledger nuances.
 */
export function getBookingStatusPresentation(
  booking: BookingStatusInput,
  now: Date = new Date(),
): BookingStatusPresentation {
  if (booking.status === BookingStatus.CANCELLED) {
    return { label: "Cancelled", tone: "neutral" };
  }

  if (booking.status === BookingStatus.EXPIRED) {
    return { label: "Expired", tone: "red" };
  }

  if (booking.status === BookingStatus.NO_SHOW) {
    return { label: "No-show", tone: "neutral" };
  }

  if (booking.status === BookingStatus.COMPLETED) {
    return { label: "Completed", tone: "teal" };
  }

  if (booking.status === BookingStatus.CONFIRMED) {
    return { label: "Confirmed", tone: "green" };
  }

  if (isPendingBooking(booking)) {
    if (isBookingReservationExpired(booking, now)) {
      return { label: "Hold expired", tone: "red" };
    }

    const paymentStatus = booking.payment_status;
    if (
      paymentStatus == null ||
      paymentStatus === BookingPaymentStatus.PENDING ||
      paymentStatus === BookingPaymentStatus.UNPAID
    ) {
      return { label: "Pending payment", tone: "amber" };
    }

    if (paymentStatus === BookingPaymentStatus.FAILED) {
      return { label: "Payment failed", tone: "red" };
    }

    return { label: "Pending", tone: "amber" };
  }

  return { label: formatUnknownStatus(booking.status), tone: "neutral" };
}

function formatUnknownStatus(status: string): string {
  if (!status) return "Unknown";
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
