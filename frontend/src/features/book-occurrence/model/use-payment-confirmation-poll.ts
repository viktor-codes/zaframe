"use client";

import { useEffect, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchBooking, getUserFacingApiMessage } from "@shared/api";
import {
  getGuestBookingAccessToken,
  parsePositiveIdString,
  queryKeys,
  useNow,
} from "@shared/lib";

import {
  resolvePaymentConfirmation,
  shouldContinuePaymentConfirmationPoll,
  type PaymentConfirmationResult,
} from "./resolve-payment-confirmation";

const POLL_INTERVAL_MS = 2_000;
/** Soft UX hint only — polling continues until terminal phase or hard timeout. */
const SLOW_WEBHOOK_HINT_AFTER_MS = 60_000;
/** Stop polling after this wall-clock window (battery / runaway requests). */
const POLL_HARD_TIMEOUT_MS = 5 * 60_000;

const TERMINAL_SUCCESS_PHASES = new Set(["confirmed", "manual_review"]);

export interface UsePaymentConfirmationPollResult {
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  confirmation: PaymentConfirmationResult | null;
  isWebhookSlow: boolean;
  hasTimedOut: boolean;
  bookingId: number | null;
}

/**
 * Poll GET /bookings/{id} after Stripe redirect until webhook confirms payment.
 */
export function usePaymentConfirmationPoll(
  bookingIdParam: string | null,
): UsePaymentConfirmationPollResult {
  const queryClient = useQueryClient();
  const bookingId = parsePositiveIdString(bookingIdParam);
  const [pollStartedAt] = useState(() => Date.now());

  const query = useQuery({
    queryKey: queryKeys.booking.detail(bookingId ?? 0),
    queryFn: ({ signal }) => {
      const accessToken =
        bookingId != null ? getGuestBookingAccessToken(bookingId) : null;
      return fetchBooking(bookingId!, { accessToken, signal });
    },
    enabled: bookingId != null,
    retry: false,
    refetchInterval: (q) => {
      if (Date.now() - pollStartedAt >= POLL_HARD_TIMEOUT_MS) {
        return false;
      }
      const data = q.state.data;
      if (!data) return POLL_INTERVAL_MS;
      const result = resolvePaymentConfirmation(data);
      return shouldContinuePaymentConfirmationPoll(result)
        ? POLL_INTERVAL_MS
        : false;
    },
  });

  const confirmation =
    query.data != null ? resolvePaymentConfirmation(query.data) : null;
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
      // WHY: account lists can stay stale for staleTime after webhook confirms.
      void queryClient.invalidateQueries({ queryKey: queryKeys.bookings.all });
    }
  }, [confirmation, queryClient]);

  if (bookingId == null) {
    return {
      isLoading: false,
      isError: true,
      errorMessage:
        "Missing booking reference. Return from checkout and try again.",
      confirmation: null,
      isWebhookSlow: false,
      hasTimedOut: false,
      bookingId: null,
    };
  }

  return {
    isLoading: query.isLoading && !query.data,
    isError: query.isError,
    errorMessage: query.isError ? getUserFacingApiMessage(query.error) : null,
    confirmation,
    isWebhookSlow,
    hasTimedOut,
    bookingId,
  };
}
