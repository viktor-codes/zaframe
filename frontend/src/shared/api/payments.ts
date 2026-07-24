/**
 * Payments API (Stripe Checkout).
 */

import type {
  CheckoutSessionCreate,
  CheckoutSessionResponse,
} from "@entities/booking";

import { api, createIdempotencyKey, type RequestConfig } from "./client";

export async function createCheckoutSession(
  data: CheckoutSessionCreate,
  options?: Pick<RequestConfig, "idempotencyKey" | "requestId">,
): Promise<CheckoutSessionResponse> {
  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/checkout-session",
    data,
    {
      skipAuth: true,
      idempotencyKey: options?.idempotencyKey ?? createIdempotencyKey(),
      requestId: options?.requestId,
    },
  );
}
