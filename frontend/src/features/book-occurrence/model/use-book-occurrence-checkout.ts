"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { OccurrenceResponse } from "@entities/occurrence";
import {
  createBooking,
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
} from "@shared/api";
import { getSafeStripeCheckoutUrl, storeGuestBookingAccess } from "@shared/lib";

import {
  getBookingCheckoutErrorMessage,
  isOccurrenceFullCheckoutError,
} from "./booking-edge-messages";
import type { GuestDetails } from "./guest-details-schema";

export interface BookOccurrenceCheckoutInput {
  occurrence: OccurrenceResponse;
  guest: GuestDetails;
}

type CheckoutMutationResult =
  | { kind: "stripe"; bookingId: number }
  | { kind: "free"; bookingId: number }
  | { kind: "checkout_failed"; bookingId: number; message: string };

const CHECKOUT_FAILED_FALLBACK =
  "Payment could not be started. Your seat is held — open booking details to retry.";

export function useBookOccurrenceCheckout() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isOccurrenceFull, setIsOccurrenceFull] = useState(false);
  const [heldBookingId, setHeldBookingId] = useState<number | null>(null);
  const checkoutIdempotencyKeyRef = useRef(createIdempotencyKey());

  const mutation = useMutation({
    mutationFn: async ({
      occurrence,
      guest,
    }: BookOccurrenceCheckoutInput): Promise<CheckoutMutationResult> => {
      const booking = await createBooking({
        occurrence_id: occurrence.id,
        guest_name: guest.guest_name,
        guest_email: guest.guest_email,
        guest_phone: guest.guest_phone,
        booking_type: "single",
        service_id: occurrence.service_id,
      });

      storeGuestBookingAccess(booking.id, booking.access_token, {
        id: booking.id,
        occurrence_id: booking.occurrence_id,
        guest_name: booking.guest_name ?? null,
        guest_email: booking.guest_email ?? null,
        status: booking.status,
        payment_status: booking.payment_status ?? null,
        reserved_until: booking.reserved_until ?? null,
      });

      // WHY: free sessions have no Stripe Checkout — confirm page is the success UI.
      if (occurrence.price_cents === 0) {
        return { kind: "free", bookingId: booking.id };
      }

      const origin = window.location.origin;

      try {
        const session = await createCheckoutSession(
          {
            booking_id: booking.id,
            success_url: `${origin}/bookings/success?booking=${booking.id}`,
            cancel_url: `${origin}/bookings/cancel?booking=${booking.id}`,
            access_token: booking.access_token,
          },
          { idempotencyKey: checkoutIdempotencyKeyRef.current },
        );

        const checkoutUrl = getSafeStripeCheckoutUrl(session.checkout_url);
        if (checkoutUrl) {
          window.location.href = checkoutUrl;
          return { kind: "stripe", bookingId: booking.id };
        }

        return {
          kind: "checkout_failed",
          bookingId: booking.id,
          message: CHECKOUT_FAILED_FALLBACK,
        };
      } catch (err) {
        return {
          kind: "checkout_failed",
          bookingId: booking.id,
          message: getUserFacingApiMessage(err) || CHECKOUT_FAILED_FALLBACK,
        };
      }
    },
    onSuccess: (result) => {
      if (result.kind === "stripe") return;

      if (result.kind === "free") {
        router.push(`/bookings/${result.bookingId}/confirm`);
        return;
      }

      setHeldBookingId(result.bookingId);
      setIsOccurrenceFull(false);
      setError(result.message);
    },
    onError: (err) => {
      setHeldBookingId(null);
      setIsOccurrenceFull(isOccurrenceFullCheckoutError(err));
      setError(getBookingCheckoutErrorMessage(err));
    },
  });

  return {
    error,
    isOccurrenceFull,
    heldBookingId,
    clearError: () => {
      setError(null);
      setIsOccurrenceFull(false);
      setHeldBookingId(null);
    },
    isPaying: mutation.isPending,
    pay: (input: BookOccurrenceCheckoutInput) => {
      setError(null);
      setIsOccurrenceFull(false);
      setHeldBookingId(null);
      mutation.mutate(input);
    },
  };
}
