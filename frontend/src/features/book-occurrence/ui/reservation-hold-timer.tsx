"use client";

import { useEffect, useState } from "react";
import {
  getBookingReservationRemainingMs,
  isPendingBooking,
} from "@entities/booking";
import { Alert } from "@shared/ui";

export interface ReservationHoldTimerProps {
  status: string;
  reservedUntil: string | null | undefined;
}

function formatRemaining(ms: number): string {
  const totalSeconds = Math.ceil(ms / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

/**
 * Live countdown for a pending unpaid hold (`reserved_until`).
 */
export function ReservationHoldTimer({
  status,
  reservedUntil,
}: ReservationHoldTimerProps) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    if (!isPendingBooking({ status }) || !reservedUntil) return;
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, [status, reservedUntil]);

  if (!isPendingBooking({ status })) return null;

  const remainingMs = getBookingReservationRemainingMs(
    { status, reserved_until: reservedUntil ?? null },
    now,
  );

  if (remainingMs == null) return null;

  if (remainingMs <= 0) {
    return (
      <Alert
        variant="error"
        title="Hold expired"
        data-testid="reservation-hold-expired"
      >
        Your seat hold has timed out. Start a new booking to reserve again.
      </Alert>
    );
  }

  return (
    <Alert
      variant="info"
      title="Complete payment to keep your seat"
      data-testid="reservation-hold-timer"
    >
      Seat held for {formatRemaining(remainingMs)}. Pay before the timer runs
      out.
    </Alert>
  );
}
