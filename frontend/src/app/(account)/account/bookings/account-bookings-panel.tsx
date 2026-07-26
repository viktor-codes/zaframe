"use client";

import { MyBookingsPanel } from "@features/view-my-bookings";
import { BookingCardActions } from "./booking-card-actions";

/**
 * Account route composition: list feature + pay/cancel actions.
 * WHY: cancel-booking is a sibling feature — wire it here, not inside view-my-bookings.
 */
export function AccountBookingsPanel() {
  return (
    <MyBookingsPanel
      renderActions={({ booking, now, bucket }) =>
        bucket === "upcoming" ? (
          <BookingCardActions booking={booking} now={now} />
        ) : null
      }
    />
  );
}
