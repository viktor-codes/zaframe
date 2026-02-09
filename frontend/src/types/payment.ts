/**
 * Типы платежей (Stripe) по backend schemas.
 */

export interface CheckoutSessionCreate {
  booking_id: number;
  success_url: string;
  cancel_url: string;
}

export interface CheckoutSessionResponse {
  checkout_url: string;
  session_id: string;
}
