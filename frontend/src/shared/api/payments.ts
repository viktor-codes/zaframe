/**
 * Payments API (Stripe Checkout).
 *
 * Idempotency-Key is required from the caller so retries reuse the same key.
 */

import type {
  CheckoutSessionCreate,
  CheckoutSessionResponse,
} from "@entities/booking";

import { api, type RequestConfig } from "./client";

export interface CreateCheckoutSessionOptions {
  /** Stable for one logical pay attempt (reuse across retries / double-submit). */
  idempotencyKey: string;
  requestId?: string;
}

export async function createCheckoutSession(
  data: CheckoutSessionCreate,
  options: CreateCheckoutSessionOptions,
): Promise<CheckoutSessionResponse> {
  const requestConfig: RequestConfig = {
    skipAuth: true,
    idempotencyKey: options.idempotencyKey,
    requestId: options.requestId,
  };

  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/checkout-session",
    data,
    requestConfig,
  );
}
