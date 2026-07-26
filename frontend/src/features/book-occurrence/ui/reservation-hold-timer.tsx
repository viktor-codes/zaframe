"use client";

import { Alert } from "@shared/ui";

import { useReservationHoldClock } from "../model/use-reservation-hold-clock";

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
  const { remainingMs, isExpired } = useReservationHoldClock(
    status,
    reservedUntil,
  );

  if (remainingMs == null && !isExpired) return null;

  if (isExpired || (remainingMs != null && remainingMs <= 0)) {
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

  if (remainingMs == null) return null;

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
