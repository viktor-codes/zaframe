"use client";

import { Skeleton } from "@shared/ui";

import { usePaymentConfirmationPoll } from "../model/use-payment-confirmation-poll";
import {
  PaymentConfirmedState,
  PaymentFailedState,
  PaymentLoadErrorState,
  PaymentManualReviewState,
  PaymentProcessingState,
  PaymentWebhookTimeoutState,
} from "./payment-success-states";

export interface PaymentSuccessPanelProps {
  bookingIdParam: string | null;
}

export function PaymentSuccessPanel({
  bookingIdParam,
}: PaymentSuccessPanelProps) {
  const {
    isLoading,
    isError,
    errorMessage,
    confirmation,
    isWebhookSlow,
    hasTimedOut,
    bookingId,
  } = usePaymentConfirmationPoll(bookingIdParam);

  if (isLoading) {
    return (
      <div data-testid="payment-success-loading">
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError) {
    return (
      <PaymentLoadErrorState
        errorMessage={errorMessage}
        bookingId={bookingId}
      />
    );
  }

  if (
    hasTimedOut &&
    (confirmation == null || confirmation.phase === "processing")
  ) {
    return <PaymentWebhookTimeoutState bookingId={bookingId} />;
  }

  if (confirmation == null || confirmation.phase === "processing") {
    return <PaymentProcessingState isWebhookSlow={isWebhookSlow} />;
  }

  if (confirmation.phase === "confirmed" && bookingId != null) {
    return <PaymentConfirmedState bookingId={bookingId} />;
  }

  if (confirmation.phase === "manual_review" && bookingId != null) {
    return <PaymentManualReviewState bookingId={bookingId} />;
  }

  if (confirmation.phase === "failed") {
    return (
      <PaymentFailedState reason={confirmation.reason} bookingId={bookingId} />
    );
  }

  return <PaymentProcessingState isWebhookSlow={isWebhookSlow} />;
}
