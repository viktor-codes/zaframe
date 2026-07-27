"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import type { OccurrenceResponse } from "@entities/occurrence";

import {
  getBookingCheckoutErrorMessage,
  isOccurrenceFullCheckoutError,
} from "./booking-edge-messages";
import { executeBookOccurrenceCheckout } from "./execute-book-occurrence-checkout";
import type { GuestDetails } from "./guest-details-schema";

export interface BookOccurrenceCheckoutInput {
  occurrence: OccurrenceResponse;
  guest: GuestDetails;
}

export function useBookOccurrenceCheckout() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isOccurrenceFull, setIsOccurrenceFull] = useState(false);
  const [heldBookingId, setHeldBookingId] = useState<number | null>(null);
  // WHY: mutationFn may run with a stale render; ref is source of truth for retry.
  const heldBookingIdRef = useRef<number | null>(null);
  // WHY: one Idempotency-Key per booking id — never reuse across different holds.
  const checkoutKeyByBookingRef = useRef<Map<number, string>>(new Map());
  // WHY: one create Idempotency-Key per occurrence+email intent (multi-tab / retry).
  const createKeyByIntentRef = useRef<Map<string, string>>(new Map());
  // WHY: isPending updates only after re-render — sync guard blocks double-click races.
  const isPayInFlightRef = useRef(false);

  const setHeld = (bookingId: number | null) => {
    heldBookingIdRef.current = bookingId;
    setHeldBookingId(bookingId);
  };

  const mutation = useMutation({
    mutationFn: (input: BookOccurrenceCheckoutInput) =>
      executeBookOccurrenceCheckout({
        ...input,
        heldBookingId: heldBookingIdRef.current,
        checkoutKeyByBooking: checkoutKeyByBookingRef.current,
        createKeyByIntent: createKeyByIntentRef.current,
        origin: window.location.origin,
        redirectTo: (url) => {
          window.location.href = url;
        },
      }),
    onSuccess: (result) => {
      if (result.kind === "stripe") return;

      if (result.kind === "free") {
        router.push(`/bookings/${result.bookingId}/confirm`);
        return;
      }

      setHeld(result.bookingId);
      setIsOccurrenceFull(false);
      setError(result.message);
    },
    onError: (err) => {
      // WHY: create failed — no seat held yet; clear any stale hold UI.
      setHeld(null);
      setIsOccurrenceFull(isOccurrenceFullCheckoutError(err));
      setError(getBookingCheckoutErrorMessage(err));
    },
    onSettled: () => {
      isPayInFlightRef.current = false;
    },
  });

  return {
    error,
    isOccurrenceFull,
    heldBookingId,
    clearError: () => {
      setError(null);
      setIsOccurrenceFull(false);
      setHeld(null);
    },
    isPaying: mutation.isPending,
    pay: (input: BookOccurrenceCheckoutInput) => {
      if (isPayInFlightRef.current || mutation.isPending) return;
      isPayInFlightRef.current = true;
      setError(null);
      setIsOccurrenceFull(false);
      // WHY: keep heldBookingId so retry does not create a second hold.
      mutation.mutate(input);
    },
  };
}
