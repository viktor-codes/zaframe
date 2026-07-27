"use client";

import { Skeleton } from "@shared/ui";

import { useOrderPaymentConfirmationPoll } from "../model/use-order-payment-confirmation-poll";
import {
  OrderPaymentConfirmedState,
  OrderPaymentFailedState,
  OrderPaymentLoadErrorState,
  OrderPaymentManualReviewState,
  OrderPaymentProcessingState,
  OrderPaymentWebhookTimeoutState,
} from "./order-payment-success-states";

export interface OrderPaymentSuccessPanelProps {
  orderIdParam: string | null;
}

export function OrderPaymentSuccessPanel({
  orderIdParam,
}: OrderPaymentSuccessPanelProps) {
  const {
    isLoading,
    isError,
    errorMessage,
    confirmation,
    isWebhookSlow,
    hasTimedOut,
    orderId,
  } = useOrderPaymentConfirmationPoll(orderIdParam);

  if (isLoading) {
    return (
      <div data-testid="order-payment-success-loading">
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (isError) {
    return <OrderPaymentLoadErrorState errorMessage={errorMessage} />;
  }

  if (
    hasTimedOut &&
    (confirmation == null || confirmation.phase === "processing")
  ) {
    return <OrderPaymentWebhookTimeoutState orderId={orderId} />;
  }

  if (confirmation == null || confirmation.phase === "processing") {
    return <OrderPaymentProcessingState isWebhookSlow={isWebhookSlow} />;
  }

  if (confirmation.phase === "confirmed") {
    return <OrderPaymentConfirmedState />;
  }

  if (confirmation.phase === "manual_review") {
    return <OrderPaymentManualReviewState />;
  }

  if (confirmation.phase === "failed") {
    return <OrderPaymentFailedState reason={confirmation.reason} />;
  }

  return <OrderPaymentProcessingState isWebhookSlow={isWebhookSlow} />;
}
