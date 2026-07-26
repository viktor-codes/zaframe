"use client";

import type { ReactNode } from "react";
import {
  bookingNeedsCheckoutPayment,
  getStudioRebookHref,
  isBookingPaymentSucceeded,
  isConfirmedBooking,
  isSessionCancelledByStudio,
} from "@entities/booking";
import { BookingStatus, useNow } from "@shared/lib";

import { useGuestBookingConfirm } from "../model/use-guest-booking-confirm";
import { useReservationHoldClock } from "../model/use-reservation-hold-clock";
import { GuestBookingConfirmDetails } from "./guest-booking-confirm-details";
import {
  GuestConfirmInactive,
  GuestConfirmLoading,
  GuestConfirmNotFound,
} from "./guest-booking-confirm-states";

export interface GuestConfirmCancelContext {
  bookingId: number;
  booking: { status: string; cancelled_at: string | null };
  occurrence: { start_time: string };
  studio: { cancel_before_hours: number };
  accessToken: string | null;
  now: Date;
}

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

  const backHref = isGuestSession ? "/studios" : "/account/bookings";
  const backLabel = isGuestSession ? "← Browse studios" : "← My bookings";

  if (isNotFound || bookingId == null) return <GuestConfirmNotFound />;
  if (isLoading || !booking) return <GuestConfirmLoading />;

  const isCancelled = booking.status === BookingStatus.CANCELLED;
  const isExpired = booking.status === BookingStatus.EXPIRED;
  const isStudioCancelled =
    occurrence != null && isSessionCancelledByStudio(occurrence);
  if (isCancelled || isExpired || isStudioCancelled) {
    const inactiveKind = isExpired
      ? "expired"
      : isStudioCancelled
        ? "studio_cancelled"
        : "cancelled";
    return (
      <GuestConfirmInactive
        kind={inactiveKind}
        backHref={backHref}
        backLabel={backLabel}
        rebookHref={
          studio != null ? getStudioRebookHref(studio) : "/studios"
        }
        studioCancelReason={
          occurrence?.cancellation_reason?.trim() || null
        }
      />
    );
  }

  const isPaid =
    isConfirmedBooking(booking) || isBookingPaymentSucceeded(booking);
  const needsPayment =
    occurrence != null && bookingNeedsCheckoutPayment(booking, occurrence);
  const canPay = needsPayment && !holdClock.isExpired;
  const cancelledAt =
    "cancelled_at" in booking ? (booking.cancelled_at ?? null) : null;

  const cancelSlot =
    renderCancel != null && occurrence != null && studio != null
      ? renderCancel({
          bookingId: booking.id,
          booking: {
            status: booking.status,
            cancelled_at: cancelledAt,
          },
          occurrence,
          studio,
          accessToken,
          now,
        })
      : null;

  return (
    <GuestBookingConfirmDetails
      bookingId={booking.id}
      guestName={booking.guest_name}
      guestEmail={booking.guest_email}
      bookingStatus={booking.status}
      paymentStatus={booking.payment_status}
      reservedUntil={reservedUntil}
      studioName={studio?.name}
      occurrenceTitle={occurrence?.title}
      occurrenceStart={occurrence?.start_time}
      priceCents={occurrence?.price_cents}
      backHref={backHref}
      backLabel={backLabel}
      needsPayment={needsPayment}
      canPay={canPay}
      isHoldExpired={needsPayment && holdClock.isExpired}
      isPaid={isPaid}
      isFreeUnpaid={
        occurrence != null && occurrence.price_cents === 0 && !isPaid
      }
      error={error}
      isPaying={isPaying}
      onPay={pay}
      cancelSlot={cancelSlot}
    />
  );
}
