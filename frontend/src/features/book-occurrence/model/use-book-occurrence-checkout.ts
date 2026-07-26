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
import { storeGuestBookingAccess } from "@shared/lib";

import type { GuestDetails } from "./guest-details-schema";

export interface BookOccurrenceCheckoutInput {
  occurrence: OccurrenceResponse;
  guest: GuestDetails;
}

export function useBookOccurrenceCheckout() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const checkoutIdempotencyKeyRef = useRef(createIdempotencyKey());

  const mutation = useMutation({
    mutationFn: async ({ occurrence, guest }: BookOccurrenceCheckoutInput) => {
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

        if (session.checkout_url) {
          window.location.href = session.checkout_url;
          return { bookingId: booking.id, redirectedToStripe: true };
        }
      } catch {
        // WHY: hold already exists — confirm page can retry Pay.
      }

      router.push(`/bookings/${booking.id}/confirm`);
      return { bookingId: booking.id, redirectedToStripe: false };
    },
    onError: (err) => {
      setError(getUserFacingApiMessage(err));
    },
  });

  return {
    error,
    clearError: () => setError(null),
    isPaying: mutation.isPending,
    pay: (input: BookOccurrenceCheckoutInput) => {
      setError(null);
      mutation.mutate(input);
    },
  };
}
