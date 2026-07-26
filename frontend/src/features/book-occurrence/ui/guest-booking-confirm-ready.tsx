import type { ReactNode } from "react";
import {
  bookingNeedsCheckoutPayment,
  getStudioRebookHref,
  isBookingPaymentSucceeded,
  isConfirmedBooking,
  isSessionCancelledByStudio,
} from "@entities/booking";
import { BookingStatus } from "@shared/lib";

import type { ResolvedGuestBooking } from "../model/use-guest-booking-confirm";
import { GuestBookingConfirmDetails } from "./guest-booking-confirm-details";
import { GuestConfirmInactive } from "./guest-booking-confirm-states";
import { guestConfirmTimelineSlot } from "./guest-booking-confirm-timeline";
import type { GuestConfirmCancelContext } from "./guest-confirm-cancel-context";

type OccurrenceData = {
  start_time: string;
  end_time: string;
  status: string;
  title?: string | null;
  price_cents: number;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
};

type StudioData = {
  name?: string | null;
  slug?: string | null;
  cancel_before_hours: number;
};

export interface GuestBookingConfirmReadyProps {
  booking: ResolvedGuestBooking;
  occurrence: OccurrenceData | undefined;
  studio: StudioData | undefined;
  reservedUntil: string | null;
  isHoldExpired: boolean;
  isGuestSession: boolean;
  accessToken: string | null;
  now: Date;
  error: string | null;
  isPaying: boolean;
  onPay: () => void;
  renderCancel?: (ctx: GuestConfirmCancelContext) => ReactNode;
}

export function GuestBookingConfirmReady({
  booking,
  occurrence,
  studio,
  reservedUntil,
  isHoldExpired,
  isGuestSession,
  accessToken,
  now,
  error,
  isPaying,
  onPay,
  renderCancel,
}: GuestBookingConfirmReadyProps) {
  const backHref = isGuestSession ? "/studios" : "/account/bookings";
  const backLabel = isGuestSession ? "← Browse studios" : "← My bookings";
  const cancelledAt =
    "cancelled_at" in booking ? (booking.cancelled_at ?? null) : null;
  const timelineSlot = guestConfirmTimelineSlot(
    {
      status: booking.status,
      created_at: "created_at" in booking ? booking.created_at : undefined,
      reserved_until: reservedUntil,
      cancelled_at: cancelledAt,
      checked_in_at:
        "checked_in_at" in booking ? (booking.checked_in_at ?? null) : null,
      no_show_at:
        "no_show_at" in booking ? (booking.no_show_at ?? null) : null,
    },
    occurrence,
  );

  const isCancelled = booking.status === BookingStatus.CANCELLED;
  const isExpired = booking.status === BookingStatus.EXPIRED;
  const isStudioCancelled =
    occurrence != null && isSessionCancelledByStudio(occurrence);

  if (isCancelled || isExpired || isStudioCancelled) {
    const kind = isExpired
      ? "expired"
      : isStudioCancelled
        ? "studio_cancelled"
        : "cancelled";
    return (
      <GuestConfirmInactive
        kind={kind}
        backHref={backHref}
        backLabel={backLabel}
        rebookHref={studio != null ? getStudioRebookHref(studio) : "/studios"}
        studioCancelReason={occurrence?.cancellation_reason?.trim() || null}
        timelineSlot={timelineSlot}
      />
    );
  }

  const isPaid =
    isConfirmedBooking(booking) || isBookingPaymentSucceeded(booking);
  const needsPayment =
    occurrence != null && bookingNeedsCheckoutPayment(booking, occurrence);

  const cancelSlot =
    renderCancel != null && occurrence != null && studio != null
      ? renderCancel({
          bookingId: booking.id,
          booking: { status: booking.status, cancelled_at: cancelledAt },
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
      canPay={needsPayment && !isHoldExpired}
      isHoldExpired={needsPayment && isHoldExpired}
      isPaid={isPaid}
      isFreeUnpaid={
        occurrence != null && occurrence.price_cents === 0 && !isPaid
      }
      error={error}
      isPaying={isPaying}
      onPay={onPay}
      timelineSlot={timelineSlot}
      cancelSlot={cancelSlot}
    />
  );
}
