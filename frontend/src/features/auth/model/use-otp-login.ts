"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getUserFacingApiMessage } from "@shared/api";
import { useAuth } from "@shared/auth";
import { getSafeNextPath } from "@shared/lib";
import { requestOtp, verifyOtp } from "../api";

export type OtpStep = "request" | "code";

const CODE_LENGTH = 6;

export interface OtpLoginController {
  step: OtpStep;
  email: string;
  name: string;
  code: string;
  isSubmitting: boolean;
  error: string | null;
  setEmail: (value: string) => void;
  setName: (value: string) => void;
  setCode: (value: string) => void;
  submitRequest: (e: React.FormEvent) => void;
  submitCode: (e: React.FormEvent) => void;
  resend: () => void;
  editEmail: () => void;
}

function parseBookingId(raw: string | null): number | null {
  if (!raw) return null;
  const parsed = Number(raw);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

/**
 * Two-step email OTP sign-in: request a code, then verify it.
 *
 * Attaches a pending guest booking (from the `booking_id` query param) to the
 * account on verify, so a guest who booked before signing in keeps that booking.
 */
export function useOtpLogin(): OtpLoginController {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();

  const [step, setStep] = useState<OtpStep>("request");
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // WHY: isSubmitting updates only after re-render — sync guard blocks double Enter.
  const isInFlightRef = useRef(false);

  const sendCode = useCallback(async () => {
    if (isInFlightRef.current) return;
    isInFlightRef.current = true;
    setError(null);
    setIsSubmitting(true);
    try {
      await requestOtp({ email, name });
      setStep("code");
      setCode("");
    } catch (err) {
      setError(getUserFacingApiMessage(err));
    } finally {
      isInFlightRef.current = false;
      setIsSubmitting(false);
    }
  }, [email, name]);

  const submitRequest = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      void sendCode();
    },
    [sendCode],
  );

  const submitCode = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (isInFlightRef.current) return;
      if (code.length !== CODE_LENGTH) {
        setError("Enter the 6-digit code from your email.");
        return;
      }

      isInFlightRef.current = true;
      setError(null);
      setIsSubmitting(true);

      const bookingId = parseBookingId(searchParams.get("booking_id"));
      const nextPath = getSafeNextPath(searchParams.get("next")) ?? "/";

      verifyOtp({
        email,
        code,
        ...(bookingId ? { booking_id: bookingId } : {}),
      })
        .then((res) => {
          login(res.access_token);
          router.replace(nextPath);
        })
        .catch((err) => {
          setError(getUserFacingApiMessage(err));
        })
        .finally(() => {
          isInFlightRef.current = false;
          setIsSubmitting(false);
        });
    },
    [code, email, searchParams, login, router],
  );

  const resend = useCallback(() => {
    void sendCode();
  }, [sendCode]);

  const editEmail = useCallback(() => {
    setStep("request");
    setError(null);
  }, []);

  return {
    step,
    email,
    name,
    code,
    isSubmitting,
    error,
    setEmail,
    setName,
    setCode,
    submitRequest,
    submitCode,
    resend,
    editEmail,
  };
}
