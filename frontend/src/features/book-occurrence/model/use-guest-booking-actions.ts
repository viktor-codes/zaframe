"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  cancelBooking,
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
} from "@shared/api";
import { getGuestBookingAccessToken, queryKeys } from "@shared/lib";
import type { CheckoutSessionCreate } from "@entities/booking";

export function useGuestBookingActions(bookingId: number | null) {
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);
  const checkoutIdempotencyKeyRef = useRef(createIdempotencyKey());

  const checkoutMutation = useMutation({
    mutationFn: (data: CheckoutSessionCreate) =>
      createCheckoutSession(data, {
        idempotencyKey: checkoutIdempotencyKeyRef.current,
      }),
    onSuccess: (data) => {
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: (err) => {
      setError(getUserFacingApiMessage(err));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) =>
      cancelBooking(id, {
        accessToken: getGuestBookingAccessToken(id),
      }),
    onSuccess: () => {
      if (bookingId != null) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.booking.detail(bookingId),
        });
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.bookings.all });
    },
    onError: (err) => {
      setError(getUserFacingApiMessage(err));
    },
  });

  return {
    error,
    clearError: () => setError(null),
    isPaying: checkoutMutation.isPending,
    isCancelling: cancelMutation.isPending,
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
    cancel: () => {
      if (bookingId == null) return;
      cancelMutation.mutate(bookingId);
    },
  };
}
