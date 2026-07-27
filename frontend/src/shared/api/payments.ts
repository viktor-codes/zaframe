/**
 * Payments API (Stripe Checkout + studio Connect / payouts).
 *
 * Checkout: Idempotency-Key is required from the caller so retries reuse the same key.
 *
 * Auth (checkout):
 * - Session user: send Bearer (default) so backend resolves current_user.
 * - Guest: access_token in body → skip session auth/refresh (same idea as bookings).
 *
 * Studio Connect / payouts: session Bearer only (`manage_payouts`).
 */

import type {
  CheckoutSessionCreate,
  CheckoutSessionResponse,
} from "@entities/booking";
import type { OrderCheckoutSessionCreate } from "@entities/order";

import { api, type RequestConfig } from "./client";
import type { Schema } from "./schema";

export type StripeConnectStatusResponse = Schema<"StripeConnectStatusResponse">;
export type StripeConnectOnboardCreate = Schema<"StripeConnectOnboardCreate">;
export type StripeConnectOnboardResponse =
  Schema<"StripeConnectOnboardResponse">;
export type PayoutSettingsUpdate = Schema<"PayoutSettingsUpdate">;

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

/** Stored Stripe Connect flags for a studio payout dashboard. */
export async function fetchStudioStripeStatus(
  studioId: number,
): Promise<StripeConnectStatusResponse> {
  return api.get<StripeConnectStatusResponse>(
    `api/v1/studios/${studioId}/stripe/status`,
  );
}

/**
 * Create or refresh a Stripe-hosted Connect onboarding link.
 * Caller must redirect only after validating `onboarding_url` (Stripe host).
 */
export async function createStudioStripeOnboarding(
  studioId: number,
  data: StripeConnectOnboardCreate,
): Promise<StripeConnectOnboardResponse> {
  return api.post<StripeConnectOnboardResponse>(
    `api/v1/studios/${studioId}/stripe/onboard`,
    data,
  );
}

/** Alias of Connect status under the payout-settings path (same payload). */
export async function fetchStudioPayoutSettings(
  studioId: number,
): Promise<StripeConnectStatusResponse> {
  return api.get<StripeConnectStatusResponse>(
    `api/v1/studios/${studioId}/payout-settings`,
  );
}

/**
 * Refresh Connect flags from Stripe when `refresh_from_stripe` is true.
 * WHY: return/refresh redirects land before `account.updated` may finish.
 */
export async function updateStudioPayoutSettings(
  studioId: number,
  data: PayoutSettingsUpdate,
): Promise<StripeConnectStatusResponse> {
  return api.patch<StripeConnectStatusResponse>(
    `api/v1/studios/${studioId}/payout-settings`,
    data,
  );
}
