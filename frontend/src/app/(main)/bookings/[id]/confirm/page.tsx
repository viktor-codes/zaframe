"use client";

import { useParams } from "next/navigation";
import { GuestBookingConfirmPanel } from "@features/book-occurrence";
import { CancelBookingControls } from "@features/cancel-booking";

export default function BookingConfirmPage() {
  const params = useParams();

  return (
    <GuestBookingConfirmPanel
      routeId={params.id}
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
