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
/** Soft UX hint only — polling continues until a terminal phase. */
const SLOW_WEBHOOK_HINT_AFTER_MS = 60_000;

export interface UsePaymentConfirmationPollResult {
  isLoading: boolean;
  isError: boolean;
  errorMessage: string | null;
  confirmation: PaymentConfirmationResult | null;
  isWebhookSlow: boolean;
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

  const query = useQuery({
    queryKey: queryKeys.booking.detail(bookingId ?? 0),
    queryFn: () => {
      const accessToken =
        bookingId != null ? getGuestBookingAccessToken(bookingId) : null;
      return fetchBooking(bookingId!, { accessToken });
    },
    enabled: bookingId != null,
    retry: false,
    refetchInterval: (q) => {
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
      return;
    }

    const elapsed = Date.now() - pollStartedAt;
    if (elapsed >= SLOW_WEBHOOK_HINT_AFTER_MS) {
      setIsWebhookSlow(true);
      return;
    }

    const timer = window.setTimeout(() => {
      setIsWebhookSlow(true);
    }, SLOW_WEBHOOK_HINT_AFTER_MS - elapsed);

    return () => window.clearTimeout(timer);
  }, [confirmation?.phase, pollStartedAt]);

  if (bookingId == null) {
    return {
      isLoading: false,
      isError: true,
      errorMessage:
        "Missing booking reference. Return from checkout and try again.",
      confirmation: null,
      isWebhookSlow: false,
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
    bookingId,
  };
}
