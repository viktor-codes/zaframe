import { isCancelledBooking } from "./booking";

export type BookingListBucket = "upcoming" | "past" | "cancelled";

type BookingBucketInput = {
  status: string;
  cancelled_at: string | null;
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
  if (isCancelledBooking(booking)) {
    return "cancelled";
  }

  const startMs = new Date(booking.occurrence.start_time).getTime();
  if (startMs >= now.getTime()) {
    return "upcoming";
  }

  return "past";
}

export function compareBookingsForBucket(
  bucket: BookingListBucket,
  left: BookingBucketInput & { cancelled_at?: string | null },
  right: BookingBucketInput & { cancelled_at?: string | null },
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

  const leftCancelled = left.cancelled_at
    ? new Date(left.cancelled_at).getTime()
    : 0;
  const rightCancelled = right.cancelled_at
    ? new Date(right.cancelled_at).getTime()
    : 0;
  return rightCancelled - leftCancelled;
}
