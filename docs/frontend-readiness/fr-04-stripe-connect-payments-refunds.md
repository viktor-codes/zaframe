# FR-04 — Stripe Connect, Payments, and Refunds (P1)

> This step is only required before real studio payouts/refunds UI. For a basic dashboard MVP,
> `Order.status` plus the Stripe dashboard may be enough.

## Problem

Stripe checkout exists, but the product needs a clear model for payouts, platform fees, payment
history, and refunds before the owner dashboard can show reliable money-related UI.

`Order.application_fee_cents` only becomes meaningful when Stripe Connect destination charges or
equivalent Connect flow is implemented.

FR-12 decision: paid checkout is blocked until a studio has a Connect destination that can accept
charges. Platform fee calculation/storage remains deferred; do not display or rely on platform fee
amounts in frontend flows until the fee model is implemented end-to-end.

## Goal

Add a minimal but production-shaped payment ledger and Stripe Connect onboarding/status contracts.

## Studio Connect Fields

Add to `Studio`:

- [ ] `stripe_account_id`
- [ ] `stripe_charges_enabled`
- [ ] `stripe_payouts_enabled`
- [ ] `stripe_onboarding_completed_at`
- [ ] optional `stripe_onboarding_url_expires_at`

## Order Fields

Add or confirm:

- [ ] `Order.application_fee_cents`
- [ ] `Order.payment_intent_id`
- [x] `Order.guest_phone` already exists via migration `008`.
- [x] `Order.access_token` already exists via migration `006`.

## Booking Fields

- [x] `Booking.payment_intent_id` already exists and is written on payment confirmation.
- [x] `Booking.access_token` already exists via migration `006`.
- [ ] Do not store raw guest access tokens in new fields. If new token storage is needed, store only hashes.

## Payment Model

Add `Payment`:

- [ ] `id`
- [ ] `booking_id` nullable
- [ ] `order_id` nullable
- [ ] `stripe_checkout_session_id`
- [ ] `stripe_payment_intent_id`
- [ ] `amount_cents`
- [ ] `currency`
- [ ] `status`
- [ ] `provider`
- [ ] `paid_at`
- [ ] `refunded_amount_cents`
- [ ] `created_at`
- [ ] `updated_at`

## Refund Model

Add `Refund`:

- [ ] `id`
- [ ] `payment_id`
- [ ] `stripe_refund_id`
- [ ] `amount_cents`
- [ ] `reason`
- [ ] `status`
- [ ] `created_at`

## API Contract

### Stripe Connect

- [ ] `GET /studios/{studio_id}/stripe/status`
- [ ] `POST /studios/{studio_id}/stripe/onboard`
- [ ] `GET /studios/{studio_id}/payout-settings`
- [ ] `PATCH /studios/{studio_id}/payout-settings`

### Payment history

- [ ] `GET /payments/my` for customer account if needed.
- [ ] `GET /studios/{studio_id}/payments` for owner dashboard.
- [ ] Include filters: status, date range, booking/order ID.

### Refunds

- [ ] Add minimal owner/admin refund endpoint:
  - `POST /payments/{payment_id}/refunds`
- [ ] Enforce permissions.
- [ ] Validate refundable amount.
- [ ] Update `Payment.refunded_amount_cents`.
- [ ] Update `Order.status` / `Booking.status` if applicable.

## Webhooks

- [ ] Existing checkout completion must create/update `Payment`.
- [ ] Add Stripe `account.updated` webhook.
- [ ] Keep webhook idempotency through processed event storage.
- [ ] Delayed webhook behavior must be covered by tests in [FR-05](./fr-05-booking-order-lifecycle.md).

## Tests

- [ ] Connect onboarding endpoint requires owner/manager permission.
- [ ] `account.updated` updates studio Connect flags.
- [ ] Checkout confirmation creates or updates a `Payment`.
- [ ] Duplicate webhook is idempotent.
- [ ] Refund endpoint creates `Refund` and updates payment/order state.
- [ ] Unauthorized user cannot see another studio's payments.

## Definition of Done

- [ ] Owner dashboard can show payout status.
- [ ] Owner dashboard can show payment history.
- [ ] Refund action is possible through API, not only Stripe dashboard.
- [ ] Platform fee is stored where Connect flow actually uses it.

## Out of Scope

- Full accounting exports.
- Tax reporting.
- Complex split payments.
- Automated overbooking refunds beyond the minimal refund action.
