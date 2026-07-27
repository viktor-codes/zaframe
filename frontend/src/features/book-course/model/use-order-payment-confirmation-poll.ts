"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchOrder, getUserFacingApiMessage } from "@shared/api";
import {
  getGuestOrderAccessToken,
  parsePositiveIdString,
  queryKeys,
  useNow,
} from "@shared/lib";

import {
  resolveOrderPaymentConfirmation,
  shouldContinueOrderPaymentConfirmationPoll,
  type OrderPaymentConfirmationResult,
} from "./resolve-order-payment-confirmation";

const POLL_INTERVAL_MS = 2_000;
const SLOW_WEBHOOK_HINT_AFTER_MS = 60_000;
const POLL_HARD_TIMEOUT_MS = 5 * 60_000;

const TERMINAL_SUCCESS_PHASES = new Set(["confirmed", "manual_review"]);

export interface UseOrderPaymentConfirmationPollResult {
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  confirmation: OrderPaymentConfirmationResult | null;
  isWebhookSlow: boolean;
  hasTimedOut: boolean;
  orderId: number | null;
}

/**
 * Poll GET /orders/{id} after Stripe redirect until webhook confirms payment.
 */
export function useOrderPaymentConfirmationPoll(
  orderIdParam: string | null,
): UseOrderPaymentConfirmationPollResult {
  const queryClient = useQueryClient();
  const orderId = parsePositiveIdString(orderIdParam);
  const [pollStartedAt] = useState(() => Date.now());

  const query = useQuery({
    queryKey: queryKeys.order.detail(orderId ?? 0),
    queryFn: ({ signal }) => {
      const accessToken =
        orderId != null ? getGuestOrderAccessToken(orderId) : null;
      return fetchOrder(orderId!, { accessToken, signal });
    },
    enabled: orderId != null,
    retry: false,
    refetchInterval: (q) => {
      if (Date.now() - pollStartedAt >= POLL_HARD_TIMEOUT_MS) {
        return false;
      }
      const data = q.state.data;
      if (!data) return POLL_INTERVAL_MS;
      const result = resolveOrderPaymentConfirmation(data);
      return shouldContinueOrderPaymentConfirmationPoll(result)
        ? POLL_INTERVAL_MS
        : false;
    },
  });

  const confirmation =
    query.data != null ? resolveOrderPaymentConfirmation(query.data) : null;
  const isProcessing = confirmation?.phase === "processing";
  // WHY: derive slow/timeout from a ticking clock — avoids setState-in-effect.
  const now = useNow({ enabled: isProcessing });
  const elapsedMs = isProcessing ? now.getTime() - pollStartedAt : 0;
  const isWebhookSlow = isProcessing && elapsedMs >= SLOW_WEBHOOK_HINT_AFTER_MS;
  const hasTimedOut = isProcessing && elapsedMs >= POLL_HARD_TIMEOUT_MS;

  useEffect(() => {
    if (
      confirmation != null &&
      TERMINAL_SUCCESS_PHASES.has(confirmation.phase)
    ) {
      // WHY: course payment updates both order and booking list caches.
      void queryClient.invalidateQueries({ queryKey: queryKeys.orders.all });
      void queryClient.invalidateQueries({ queryKey: queryKeys.bookings.all });
    }
  }, [confirmation, queryClient]);

  if (orderId == null) {
    return {
      isLoading: false,
      isError: true,
      errorMessage:
        "Missing order reference. Return from checkout and try again.",
      confirmation: null,
      isWebhookSlow: false,
      hasTimedOut: false,
      orderId: null,
    };
  }

  return {
    isLoading: query.isLoading && !query.data,
    isError: query.isError,
    errorMessage: query.isError ? getUserFacingApiMessage(query.error) : null,
    confirmation,
    isWebhookSlow,
    hasTimedOut,
    orderId,
  };
}
