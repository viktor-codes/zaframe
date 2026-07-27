"use client";

import { useState } from "react";
import {
  canCustomerCancelBooking,
  getCancelPolicyHint,
} from "@entities/booking";
import { Button } from "@shared/ui";
import { useCancelBooking } from "../model/use-cancel-booking";

export interface CancelBookingControlsProps {
  bookingId: number;
  booking: {
    status: string;
    cancelled_at: string | null;
    reserved_until?: string | null;
  };
  occurrence: { start_time: string };
  studio: { cancel_before_hours: number };
  accessToken?: string | null;
  now?: Date;
  className?: string;
  onCancelled?: () => void;
}

export function CancelBookingControls({
  bookingId,
  booking,
  occurrence,
  studio,
  accessToken,
  now = new Date(),
  className = "",
  onCancelled,
}: CancelBookingControlsProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const { cancelBooking, isCancelling } = useCancelBooking({
    accessToken,
    onSuccess: onCancelled,
  });

  const policyBooking = {
    status: booking.status,
    cancelled_at: booking.cancelled_at,
    reserved_until: booking.reserved_until,
  };
  const canCancel = canCustomerCancelBooking(
    policyBooking,
    occurrence,
    studio,
    now,
  );
  const policyHint = getCancelPolicyHint(
    policyBooking,
    occurrence,
    studio,
    now,
  );

  if (!policyHint) {
    return null;
  }

  if (!canCancel && policyHint.kind === "closed") {
    return (
      <p
        className={`text-xs text-neutral-500 ${className}`}
        data-testid="cancel-cutoff-closed"
      >
        Cancellation closed {policyHint.cancelBeforeHours}h before the session.
      </p>
    );
  }

  if (!canCancel) {
    return null;
  }

  if (showConfirm) {
    return (
      <div
        className={`rounded-xl border border-red-200 bg-red-50 p-3 ${className}`}
        data-testid="cancel-booking-confirm"
      >
        <p className="mb-1 text-sm font-medium text-red-800">
          Cancel this booking? This cannot be undone.
        </p>
        {policyHint.kind === "allowed" ? (
          <p className="mb-3 text-xs text-red-700/80">
            Free cancellation until {policyHint.deadlineLabel}.
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            variant="danger"
            size="sm"
            isLoading={isCancelling}
            onClick={() => cancelBooking(bookingId)}
            data-testid="confirm-cancel-booking"
          >
            Yes, cancel booking
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={isCancelling}
            onClick={() => setShowConfirm(false)}
          >
            Keep booking
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={className}>
      {policyHint.kind === "allowed" ? (
        <p className="mb-2 text-xs text-neutral-500">
          Free cancellation until {policyHint.deadlineLabel}
        </p>
      ) : null}
      <Button
        type="button"
        variant="ghost"
        size="sm"
        onClick={() => setShowConfirm(true)}
        className="text-red-600 hover:bg-red-50 hover:text-red-700"
        data-testid="cancel-booking-button"
      >
        Cancel booking
      </Button>
    </div>
  );
}
