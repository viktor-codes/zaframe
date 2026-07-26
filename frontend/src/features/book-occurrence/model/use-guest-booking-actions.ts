"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
} from "@shared/api";
import {
  getGuestBookingAccessToken,
  getSafeStripeCheckoutUrl,
} from "@shared/lib";
import type { CheckoutSessionCreate } from "@entities/booking";

const UNSAFE_CHECKOUT_URL_MESSAGE =
  "Payment could not be started. Please try again or contact the studio.";

export function useGuestBookingActions(bookingId: number | null) {
  const [error, setError] = useState<string | null>(null);
  const checkoutIdempotencyKeyRef = useRef(createIdempotencyKey());

  const checkoutMutation = useMutation({
    mutationFn: (data: CheckoutSessionCreate) =>
      createCheckoutSession(data, {
        idempotencyKey: checkoutIdempotencyKeyRef.current,
      }),
    onSuccess: (data) => {
      const checkoutUrl = getSafeStripeCheckoutUrl(data.checkout_url);
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
        return;
      }
      if (data.checkout_url) {
        setError(UNSAFE_CHECKOUT_URL_MESSAGE);
      }
    },
    onError: (err) => {
      setError(getUserFacingApiMessage(err));
    },
  });

  return {
    error,
    clearError: () => setError(null),
    isPaying: checkoutMutation.isPending,
    pay: () => {
      if (bookingId == null) return;
      setError(null);
      const origin = window.location.origin;
      const token = getGuestBookingAccessToken(bookingId);
      checkoutMutation.mutate({
        booking_id: bookingId,
        success_url: `${origin}/bookings/success?booking=${bookingId}`,
        cancel_url: `${origin}/bookings/cancel?booking=${bookingId}`,
        ...(token ? { access_token: token } : {}),
      });
    },
  };
}
