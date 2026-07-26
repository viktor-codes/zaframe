"use client";

import type { ReactNode } from "react";
import { BookingStatus, useNow } from "@shared/lib";

import { useGuestBookingConfirm } from "../model/use-guest-booking-confirm";
import { useReservationHoldClock } from "../model/use-reservation-hold-clock";
import { GuestBookingConfirmReady } from "./guest-booking-confirm-ready";
import {
  GuestConfirmLoading,
  GuestConfirmNotFound,
} from "./guest-booking-confirm-states";
import type { GuestConfirmCancelContext } from "./guest-confirm-cancel-context";

export type { GuestConfirmCancelContext };

export interface GuestBookingConfirmPanelProps {
  routeId: unknown;
  accessTokenFromQuery: string | null;
  /**
   * App-layer composition slot (e.g. CancelBookingControls).
   * WHY: features must not import other features.
   */
  renderCancel?: (ctx: GuestConfirmCancelContext) => ReactNode;
}

export function GuestBookingConfirmPanel({
  routeId,
  accessTokenFromQuery,
  renderCancel,
}: GuestBookingConfirmPanelProps) {
  const now = useNow();
  const {
    bookingId,
    booking,
    occurrence,
    studio,
    isLoading,
    isNotFound,
    isGuestSession,
    accessToken,
    error,
    isPaying,
    pay,
  } = useGuestBookingConfirm(routeId, accessTokenFromQuery);

  const reservedUntil =
    booking && "reserved_until" in booking
      ? (booking.reserved_until ?? null)
      : null;
  const holdClock = useReservationHoldClock(
    booking?.status ?? BookingStatus.PENDING,
    reservedUntil,
    now,
  );

  if (isNotFound || bookingId == null) return <GuestConfirmNotFound />;
  if (isLoading || !booking) return <GuestConfirmLoading />;

  return (
    <GuestBookingConfirmReady
      booking={booking}
      occurrence={occurrence}
      studio={studio}
      reservedUntil={reservedUntil}
      isHoldExpired={holdClock.isExpired}
      isGuestSession={isGuestSession}
      accessToken={accessToken}
      now={now}
      error={error}
      isPaying={isPaying}
      onPay={pay}
      renderCancel={renderCancel}
    />
  );
}
