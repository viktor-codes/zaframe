/**
 * Payments API (Stripe Checkout).
 *
 * Idempotency-Key is required from the caller so retries reuse the same key.
 *
 * Auth:
 * - Session user: send Bearer (default) so backend resolves current_user.
 * - Guest: access_token in body → skip session auth/refresh (same idea as bookings).
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
  const isGuestCheckout = Boolean(data.access_token);
  const requestConfig: RequestConfig = {
    skipAuth: isGuestCheckout,
    skipRefresh: isGuestCheckout,
    idempotencyKey: options.idempotencyKey,
    requestId: options.requestId,
  };

  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/checkout-session",
    data,
    requestConfig,
  );
}
