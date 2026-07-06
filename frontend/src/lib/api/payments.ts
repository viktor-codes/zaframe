/**
 * API для платежей (Stripe Checkout).
 */

import { api } from "@shared/api";
import type {
  CheckoutSessionCreate,
  CheckoutSessionResponse,
} from "@entities/booking";

export async function createCheckoutSession(
  data: CheckoutSessionCreate,
): Promise<CheckoutSessionResponse> {
  return api.post<CheckoutSessionResponse>(
    "api/v1/payments/checkout-session",
    data,
    { skipAuth: true },
  );
}
