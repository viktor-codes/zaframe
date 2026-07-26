"use client";

import Link from "next/link";
import {
  canCompleteBookingPayment,
  getBookingReservationRemainingMs,
  type BookingSelfListItem,
} from "@entities/booking";
import { CancelBookingControls } from "@features/cancel-booking";
import { Button } from "@shared/ui";

export interface BookingCardActionsProps {
  booking: BookingSelfListItem;
  now: Date;
}

function formatHoldRemaining(remainingMs: number): string {
  const totalSeconds = Math.max(Math.ceil(remainingMs / 1000), 0);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  if (minutes <= 0) {
    return `${seconds}s left to pay`;
  }
  return `${minutes}m ${seconds.toString().padStart(2, "0")}s left to pay`;
}

/**
 * Account-list actions: finish unpaid hold and/or cancel before cutoff.
 */
export function BookingCardActions({ booking, now }: BookingCardActionsProps) {
  const canPay = canCompleteBookingPayment(
    booking,
    booking.occurrence,
    now,
  );
  const remainingMs = canPay
    ? getBookingReservationRemainingMs(booking, now)
    : null;

  return (
    <div className="flex flex-col gap-3">
      {canPay ? (
        <div data-testid="booking-pay-action">
          {remainingMs != null ? (
            <p className="mb-2 text-xs text-amber-800">
              {formatHoldRemaining(remainingMs)}
            </p>
          ) : null}
          <Button asChild size="sm" data-testid="booking-complete-payment">
            <Link href={`/bookings/${booking.id}/confirm`}>
              Complete payment
            </Link>
          </Button>
        </div>
      ) : null}

      <CancelBookingControls
        bookingId={booking.id}
        booking={{
          status: booking.status,
          cancelled_at: booking.cancelled_at,
          reserved_until: booking.reserved_until,
        }}
        occurrence={booking.occurrence}
        studio={booking.studio}
        now={now}
      />
    </div>
  );
}
