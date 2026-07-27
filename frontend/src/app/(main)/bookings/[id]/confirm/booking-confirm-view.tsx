"use client";

import { GuestBookingConfirmPanel } from "@features/book-occurrence";
import { CancelBookingControls } from "@features/cancel-booking";

export interface BookingConfirmViewProps {
  routeId: string;
}

/**
 * App-layer client composition: features must not import each other,
 * so cancel controls are wired here via renderCancel.
 */
export function BookingConfirmView({ routeId }: BookingConfirmViewProps) {
  return (
    <GuestBookingConfirmPanel
      routeId={routeId}
      renderCancel={({
        bookingId,
        booking,
        occurrence,
        studio,
        accessToken,
        now,
      }) => (
        <CancelBookingControls
          bookingId={bookingId}
          booking={booking}
          occurrence={occurrence}
          studio={studio}
          accessToken={accessToken}
          now={now}
        />
      )}
    />
  );
}
