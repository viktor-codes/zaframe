"use client";

import { useState } from "react";
import {
  bookingNeedsCheckoutPayment,
  canCustomerCancelBooking,
  isBookingPaymentSucceeded,
  isConfirmedBooking,
} from "@entities/booking";
import { BookingStatus } from "@shared/lib";

import { useGuestBookingConfirm } from "../model/use-guest-booking-confirm";
import { useReservationHoldClock } from "../model/use-reservation-hold-clock";
import { GuestBookingConfirmDetails } from "./guest-booking-confirm-details";
import {
  GuestConfirmInactive,
  GuestConfirmLoading,
  GuestConfirmNotFound,
} from "./guest-booking-confirm-states";

export interface GuestBookingConfirmPanelProps {
  routeId: unknown;
  accessTokenFromQuery: string | null;
}

export function GuestBookingConfirmPanel({
  routeId,
  accessTokenFromQuery,
}: GuestBookingConfirmPanelProps) {
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);
  const {
    bookingId,
    booking,
    occurrence,
    studio,
    isLoading,
    isNotFound,
    isGuestSession,
    error,
    isPaying,
    isCancelling,
    pay,
    cancel,
  } = useGuestBookingConfirm(routeId, accessTokenFromQuery);

  const reservedUntil =
    booking && "reserved_until" in booking
      ? (booking.reserved_until ?? null)
      : null;
  const holdClock = useReservationHoldClock(
    booking?.status ?? BookingStatus.PENDING,
    reservedUntil,
  );

  const backHref = isGuestSession ? "/studios" : "/bookings";
  const backLabel = isGuestSession ? "← Browse studios" : "← My bookings";

  if (isNotFound || bookingId == null) return <GuestConfirmNotFound />;
  if (isLoading || !booking) return <GuestConfirmLoading />;

  const isCancelled = booking.status === BookingStatus.CANCELLED;
  const isExpired = booking.status === BookingStatus.EXPIRED;
  if (isCancelled || isExpired) {
    return (
      <GuestConfirmInactive
        kind={isExpired ? "expired" : "cancelled"}
        backHref={backHref}
        backLabel={backLabel}
      />
    );
  }

  const isPaid =
    isConfirmedBooking(booking) || isBookingPaymentSucceeded(booking);
  const needsPayment =
    occurrence != null && bookingNeedsCheckoutPayment(booking, occurrence);
  const canPay = needsPayment && !holdClock.isExpired;
  const isPast = occurrence
    ? new Date(occurrence.start_time).getTime() < Date.now()
    : false;
  const cancelledAt =
    "cancelled_at" in booking ? (booking.cancelled_at ?? null) : null;
  const canCancel =
    !isPast &&
    occurrence != null &&
    studio != null &&
    canCustomerCancelBooking(
      { status: booking.status, cancelled_at: cancelledAt },
      occurrence,
      studio,
    );

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
      canCancel={canCancel}
      error={error}
      isPaying={isPaying}
      isCancelling={isCancelling}
      showCancelConfirm={showCancelConfirm}
      onPay={pay}
      onAskCancel={() => setShowCancelConfirm(true)}
      onKeepBooking={() => setShowCancelConfirm(false)}
      onConfirmCancel={() => {
        cancel();
        setShowCancelConfirm(false);
      }}
    />
  );
}
