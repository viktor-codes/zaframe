"use client";

import { useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import {
  getCourseCheckoutErrorMessage,
  isCourseHardBlockCheckoutError,
} from "./course-checkout-messages";
import { executeBookCourseCheckout } from "./execute-book-course-checkout";
import type { GuestDetails } from "./guest-details-schema";

export interface BookCourseCheckoutInput {
  serviceId: number;
  guest: GuestDetails;
}

export function useBookCourseCheckout() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isHardBlocked, setIsHardBlocked] = useState(false);
  const [heldOrderId, setHeldOrderId] = useState<number | null>(null);
  const heldOrderIdRef = useRef<number | null>(null);
  const heldTotalAmountCentsRef = useRef<number | null>(null);
  const checkoutKeyByOrderRef = useRef<Map<number, string>>(new Map());
  const createKeyByIntentRef = useRef<Map<string, string>>(new Map());
  const isPayInFlightRef = useRef(false);

  const setHeld = (orderId: number | null, totalAmountCents: number | null) => {
    heldOrderIdRef.current = orderId;
    heldTotalAmountCentsRef.current = totalAmountCents;
    setHeldOrderId(orderId);
  };

  const mutation = useMutation({
    mutationFn: (input: BookCourseCheckoutInput) =>
      executeBookCourseCheckout({
        ...input,
        heldOrderId: heldOrderIdRef.current,
        heldTotalAmountCents: heldTotalAmountCentsRef.current,
        checkoutKeyByOrder: checkoutKeyByOrderRef.current,
        createKeyByIntent: createKeyByIntentRef.current,
        origin: window.location.origin,
        redirectTo: (url) => {
          window.location.href = url;
        },
      }),
    onSuccess: (result) => {
      if (result.kind === "stripe") return;

      if (result.kind === "free") {
        router.push(`/bookings/success?order=${result.orderId}`);
        return;
      }

      setHeld(result.orderId, result.totalAmountCents);
      setIsHardBlocked(false);
      setError(result.message);
    },
    onError: (err) => {
      setHeld(null, null);
      setIsHardBlocked(isCourseHardBlockCheckoutError(err));
      setError(getCourseCheckoutErrorMessage(err));
    },
    onSettled: () => {
      isPayInFlightRef.current = false;
    },
  });

  return {
    error,
    isHardBlocked,
    heldOrderId,
    clearError: () => {
      setError(null);
      setIsHardBlocked(false);
      setHeld(null, null);
    },
    isPaying: mutation.isPending,
    pay: (input: BookCourseCheckoutInput) => {
      if (isPayInFlightRef.current || mutation.isPending) return;
      isPayInFlightRef.current = true;
      setError(null);
      setIsHardBlocked(false);
      mutation.mutate(input);
    },
  };
}
