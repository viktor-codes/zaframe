import { BookingStatus } from "@shared/lib/constants";
import { isCancelledBooking } from "./booking";

export type BookingListBucket = "upcoming" | "past" | "cancelled";

type BookingBucketInput = {
  status: string;
  cancelled_at: string | null;
  updated_at?: string | null;
  occurrence: { start_time: string };
};

/**
 * Account list tab for a booking.
 * WHY: GET /bookings/my has no status/time filters — tabs are client-side.
 */
export function getBookingListBucket(
  booking: BookingBucketInput,
  now: Date = new Date(),
): BookingListBucket {
  // Expired holds belong with inactive bookings (rebook CTA on the card).
  if (
    isCancelledBooking(booking) ||
    booking.status === BookingStatus.EXPIRED
  ) {
    return "cancelled";
  }

  const startMs = new Date(booking.occurrence.start_time).getTime();
  if (startMs >= now.getTime()) {
    return "upcoming";
  }

  return "past";
}

/**
 * Sort key for the cancelled tab (newest first).
 * WHY: expired holds often have `cancelled_at = null` — fall back to updated_at,
 * then session start, so they do not all collapse to epoch 0.
 */
export function getCancelledListSortKey(booking: BookingBucketInput): number {
  if (booking.cancelled_at) {
    return new Date(booking.cancelled_at).getTime();
  }
  if (booking.updated_at) {
    return new Date(booking.updated_at).getTime();
  }
  return new Date(booking.occurrence.start_time).getTime();
}

export function compareBookingsForBucket(
  bucket: BookingListBucket,
  left: BookingBucketInput,
  right: BookingBucketInput,
): number {
  if (bucket === "upcoming") {
    return (
      new Date(left.occurrence.start_time).getTime() -
      new Date(right.occurrence.start_time).getTime()
    );
  }

  if (bucket === "past") {
    return (
      new Date(right.occurrence.start_time).getTime() -
      new Date(left.occurrence.start_time).getTime()
    );
  }

  return getCancelledListSortKey(right) - getCancelledListSortKey(left);
}
