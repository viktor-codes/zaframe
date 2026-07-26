import Link from "next/link";
import { isBookingPaymentSucceeded } from "@entities/booking";
import { formatMoneyFromCents } from "@shared/lib";
import { Alert, Button, Card } from "@shared/ui";

import {
  GuestConfirmCancelControls,
} from "./guest-booking-confirm-states";
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
  canCancel: boolean;
  error: string | null;
  isPaying: boolean;
  isCancelling: boolean;
  showCancelConfirm: boolean;
  onPay: () => void;
  onAskCancel: () => void;
  onKeepBooking: () => void;
  onConfirmCancel: () => void;
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
  canCancel,
  error,
  isPaying,
  isCancelling,
  showCancelConfirm,
  onPay,
  onAskCancel,
  onKeepBooking,
  onConfirmCancel,
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

      {needsPayment && canPay ? (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row">
          <Button
            onClick={onPay}
            isLoading={isPaying}
            data-testid="pay-booking-button"
          >
            Complete payment
          </Button>
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      ) : null}

      {needsPayment && isHoldExpired ? (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row">
          <Button asChild data-testid="rebook-after-hold-expired">
            <Link href="/studios">Book another class</Link>
          </Button>
        </div>
      ) : null}

      {isPaid ? (
        <Alert variant="success" title="Confirmed" className="mb-6">
          Your booking is confirmed
          {isBookingPaymentSucceeded({ payment_status: paymentStatus })
            ? " and paid"
            : ""}
          .
        </Alert>
      ) : null}

      {isFreeUnpaid ? (
        <Alert variant="success" title="Free session" className="mb-6">
          No payment required. Your seat is reserved
          {bookingStatus === "confirmed" ? " and confirmed" : ""}
          — check your email for details.
        </Alert>
      ) : null}

      {canCancel ? (
        <div className="mb-6">
          <GuestConfirmCancelControls
            showConfirm={showCancelConfirm}
            isCancelling={isCancelling}
            onAskConfirm={onAskCancel}
            onKeep={onKeepBooking}
            onConfirmCancel={onConfirmCancel}
          />
        </div>
      ) : null}
    </div>
  );
}
