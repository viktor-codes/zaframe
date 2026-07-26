"use client";

import { useEffect, useState } from "react";
import {
  getBookingReservationRemainingMs,
  isBookingReservationExpired,
  isPendingBooking,
} from "@entities/booking";

export interface UseReservationHoldClockResult {
  remainingMs: number | null;
  isExpired: boolean;
}

/**
 * 1s clock for pending `reserved_until` holds (timer UI + disable Pay).
 */
export function useReservationHoldClock(
  status: string,
  reservedUntil: string | null | undefined,
): UseReservationHoldClockResult {
  const [now, setNow] = useState(() => new Date());
  const isPending = isPendingBooking({ status });

  useEffect(() => {
    if (!isPending || !reservedUntil) return;
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, [isPending, reservedUntil]);

  const booking = {
    status,
    reserved_until: reservedUntil ?? null,
  };

  return {
    remainingMs: getBookingReservationRemainingMs(booking, now),
    isExpired: isBookingReservationExpired(booking, now),
  };
}
