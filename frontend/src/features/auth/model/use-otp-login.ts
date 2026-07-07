"use client";

import { useCallback, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getUserFacingApiMessage } from "@shared/api";
import { useAuth } from "@shared/auth";
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

  const sendCode = useCallback(async () => {
    setError(null);
    setIsSubmitting(true);
    try {
      await requestOtp({ email, name });
      setStep("code");
      setCode("");
    } catch (err) {
      setError(getUserFacingApiMessage(err));
    } finally {
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
      if (code.length !== CODE_LENGTH) {
        setError("Enter the 6-digit code from your email.");
        return;
      }

      setError(null);
      setIsSubmitting(true);

      const bookingId = parseBookingId(searchParams.get("booking_id"));

      verifyOtp({ email, code, ...(bookingId ? { booking_id: bookingId } : {}) })
        .then((res) => {
          login(res.access_token);
          router.replace("/");
        })
        .catch((err) => {
          setError(getUserFacingApiMessage(err));
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
