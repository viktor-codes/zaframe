import type { ReactNode } from "react";
import Link from "next/link";
import { formatMoneyFromCents } from "@shared/lib";
import { Alert, Card } from "@shared/ui";

import { GuestBookingConfirmOutcome } from "./guest-booking-confirm-outcome";
import { ReservationHoldTimer } from "./reservation-hold-timer";

export interface GuestBookingConfirmDetailsProps {
  bookingId: number;
  guestName: string | null | undefined;
  guestEmail: string | null | undefined;
  bookingStatus: string;
  paymentStatus: string | null | undefined;
  reservedUntil: string | null;
  studioName: string | null | undefined;
  occurrenceTitle: string | null | undefined;
  occurrenceStart: string | null | undefined;
  priceCents: number | null | undefined;
  backHref: string;
  backLabel: string;
  needsPayment: boolean;
  canPay: boolean;
  isHoldExpired: boolean;
  isPaid: boolean;
  isFreeUnpaid: boolean;
  error: string | null;
  isPaying: boolean;
  onPay: () => void;
  /** Entity BookingTimeline — composed by the panel when API data is ready. */
  timelineSlot?: ReactNode;
  /** Composed by app/ (e.g. CancelBookingControls) — never import features here. */
  cancelSlot?: ReactNode;
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-IE", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function GuestBookingConfirmDetails({
  bookingId,
  guestName,
  guestEmail,
  bookingStatus,
  paymentStatus,
  reservedUntil,
  studioName,
  occurrenceTitle,
  occurrenceStart,
  priceCents,
  backHref,
  backLabel,
  needsPayment,
  canPay,
  isHoldExpired,
  isPaid,
  isFreeUnpaid,
  error,
  isPaying,
  onPay,
  timelineSlot,
  cancelSlot,
}: GuestBookingConfirmDetailsProps) {
  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="guest-confirm-panel"
    >
      <div className="mb-6">
        <Link
          href={backHref}
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          {backLabel}
        </Link>
      </div>

      <h1 className="text-secondary mb-6 font-display text-2xl font-bold">
        Booking details
      </h1>

      <Card className="mb-6">
        <div className="space-y-4">
          <div>
            <p className="text-sm text-neutral-500">Booking #{bookingId}</p>
            {studioName ? (
              <p className="text-secondary font-semibold">{studioName}</p>
            ) : null}
          </div>
          {occurrenceTitle && occurrenceStart && priceCents != null ? (
            <>
              <p className="font-medium">{occurrenceTitle}</p>
              <p className="text-sm text-neutral-600">
                {formatDateTime(occurrenceStart)}
              </p>
              <p className="font-semibold text-primary">
                {priceCents === 0 ? "Free" : formatMoneyFromCents(priceCents)}
              </p>
            </>
          ) : null}
          {guestName ? (
            <p className="text-sm text-neutral-600">
              Guest: {guestName}
              {guestEmail ? ` (${guestEmail})` : ""}
            </p>
          ) : null}
        </div>
      </Card>

      {timelineSlot}

      {needsPayment ? (
        <div className="mb-6">
          <ReservationHoldTimer
            status={bookingStatus}
            reservedUntil={reservedUntil}
          />
        </div>
      ) : null}

      {error ? (
        <Alert variant="error" title="Something went wrong" className="mb-6">
          {error}
        </Alert>
      ) : null}

      <GuestBookingConfirmOutcome
        bookingStatus={bookingStatus}
        paymentStatus={paymentStatus}
        needsPayment={needsPayment}
        canPay={canPay}
        isHoldExpired={isHoldExpired}
        isPaid={isPaid}
        isFreeUnpaid={isFreeUnpaid}
        isPaying={isPaying}
        onPay={onPay}
      />

      {cancelSlot ? <div className="mb-6">{cancelSlot}</div> : null}
    </div>
  );
}
