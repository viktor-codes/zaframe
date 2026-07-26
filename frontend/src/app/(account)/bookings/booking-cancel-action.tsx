"use client";

import type { BookingSelfListItem } from "@entities/booking";
import { CancelBookingControls } from "@features/cancel-booking";

export function BookingCancelAction({
  booking,
  now,
}: {
  booking: BookingSelfListItem;
  now: Date;
}) {
  return (
    <CancelBookingControls
      bookingId={booking.id}
      booking={{
        status: booking.status,
        cancelled_at: booking.cancelled_at,
      }}
      occurrence={booking.occurrence}
      studio={booking.studio}
      now={now}
    />
  );
}
