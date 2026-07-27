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
import type { OrderCheckoutSessionCreate } from "@entities/order";

import { api, type RequestConfig } from "./client";

export interface CreateCheckoutSessionOptions {
  /** Stable for one logical pay attempt (reuse across retries / double-submit). */
  idempotencyKey: string;
  requestId?: string;
}

function checkoutRequestConfig(
  accessToken: string | null | undefined,
  options: CreateCheckoutSessionOptions,
): RequestConfig {
  const isGuestCheckout = Boolean(accessToken);
  return {
    skipAuth: isGuestCheckout,
    skipRefresh: isGuestCheckout,
    idempotencyKey: options.idempotencyKey,
    requestId: options.requestId,
  };
}

export async function createCheckoutSession(
  data: CheckoutSessionCreate,
  options: CreateCheckoutSessionOptions,
): Promise<CheckoutSessionResponse> {
  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/checkout-session",
    data,
    checkoutRequestConfig(data.access_token, options),
  );
}

/**
 * Stripe Checkout for a course order (`OrderCheckoutSessionCreate`).
 * WHY: amount and metadata come from the order, not a single booking hold.
 */
export async function createOrderCheckoutSession(
  data: OrderCheckoutSessionCreate,
  options: CreateCheckoutSessionOptions,
): Promise<CheckoutSessionResponse> {
  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/order-checkout-session",
    data,
    checkoutRequestConfig(data.access_token, options),
  );
}
