"use client";

import {
  getBookingReservationRemainingMs,
  isBookingReservationExpired,
  isPendingBooking,
} from "@entities/booking";
import { useNow } from "@shared/lib";

export interface UseReservationHoldClockResult {
  remainingMs: number | null;
  isExpired: boolean;
}

/**
 * 1s clock for pending `reserved_until` holds (timer UI + disable Pay).
 * Pass `now` from a parent clock to avoid a second interval.
 */
export function useReservationHoldClock(
  status: string,
  reservedUntil: string | null | undefined,
  nowOverride?: Date,
): UseReservationHoldClockResult {
  const isPending = isPendingBooking({ status });
  const tickingNow = useNow({
    enabled: nowOverride == null && isPending && Boolean(reservedUntil),
  });
  const now = nowOverride ?? tickingNow;

  const booking = {
    status,
    reserved_until: reservedUntil ?? null,
  };

  return {
    remainingMs: getBookingReservationRemainingMs(booking, now),
    isExpired: isBookingReservationExpired(booking, now),
  };
}
