"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchBooking, getUserFacingApiMessage } from "@shared/api";
import {
  getGuestBookingAccessToken,
  queryKeys,
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

export interface UsePaymentConfirmationPollResult {
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  confirmation: PaymentConfirmationResult | null;
  isWebhookSlow: boolean;
  hasTimedOut: boolean;
  bookingId: number | null;
}

function parseBookingId(raw: string | null): number | null {
  if (raw == null || raw.trim() === "") return null;
  const id = Number(raw);
  if (!Number.isInteger(id) || id <= 0) return null;
  return id;
}

/**
 * Poll GET /bookings/{id} after Stripe redirect until webhook confirms payment.
 */
export function usePaymentConfirmationPoll(
  bookingIdParam: string | null,
): UsePaymentConfirmationPollResult {
  const bookingId = parseBookingId(bookingIdParam);
  const [pollStartedAt] = useState(() => Date.now());
  const [isWebhookSlow, setIsWebhookSlow] = useState(false);
  const [hasTimedOut, setHasTimedOut] = useState(false);

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

  useEffect(() => {
    if (confirmation?.phase !== "processing") {
      setIsWebhookSlow(false);
      setHasTimedOut(false);
      return;
    }

    const elapsed = Date.now() - pollStartedAt;
    if (elapsed >= POLL_HARD_TIMEOUT_MS) {
      setHasTimedOut(true);
      setIsWebhookSlow(true);
      return;
    }

    if (elapsed >= SLOW_WEBHOOK_HINT_AFTER_MS) {
      setIsWebhookSlow(true);
    }

    const slowTimer = window.setTimeout(() => {
      setIsWebhookSlow(true);
    }, Math.max(SLOW_WEBHOOK_HINT_AFTER_MS - elapsed, 0));

    const hardTimer = window.setTimeout(() => {
      setHasTimedOut(true);
    }, POLL_HARD_TIMEOUT_MS - elapsed);

    return () => {
      window.clearTimeout(slowTimer);
      window.clearTimeout(hardTimer);
    };
  }, [confirmation?.phase, pollStartedAt]);

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
    errorMessage: query.isError
      ? getUserFacingApiMessage(query.error)
      : null,
    confirmation,
    isWebhookSlow,
    hasTimedOut:
      hasTimedOut ||
      (confirmation?.phase === "processing" &&
        Date.now() - pollStartedAt >= POLL_HARD_TIMEOUT_MS),
    bookingId,
  };
}
