"use client";

import {
  getBookingAccountEdge,
  type BookingSelfListItem,
} from "@entities/booking";
import { CancelBookingControls } from "@features/cancel-booking";

export function BookingCancelAction({
  booking,
  now,
}: {
  booking: BookingSelfListItem;
  now: Date;
}) {
  // WHY: expired holds already show a rebook CTA on the card.
  if (getBookingAccountEdge(booking, now)?.kind === "expired") {
    return null;
  }

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
