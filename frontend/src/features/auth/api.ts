/**
 * Email OTP auth API (passwordless login flow).
 *
 * Session refresh/logout live in `@shared/auth/api`.
 */
import { api } from "@shared/api";
import type { components } from "@shared/api";

type OtpRequestPayload = components["schemas"]["OTPRequest"];
type OtpSentResponse = components["schemas"]["OTPSentResponse"];
type OtpVerifyPayload = components["schemas"]["OTPVerify"];
type OtpVerifyResponse = components["schemas"]["OTPVerifyResponse"];

/** Ask the backend to email a 6-digit sign-in code. */
export async function requestOtp(
  payload: OtpRequestPayload,
): Promise<OtpSentResponse> {
  return api.post<OtpSentResponse>("api/v1/auth/otp/request", payload, {
    skipAuth: true,
  });
}

/** Verify the emailed code and start a session (returns the access token). */
export async function verifyOtp(
  payload: OtpVerifyPayload,
): Promise<OtpVerifyResponse> {
  return api.post<OtpVerifyResponse>("api/v1/auth/otp/verify", payload, {
    skipAuth: true,
  });
}
