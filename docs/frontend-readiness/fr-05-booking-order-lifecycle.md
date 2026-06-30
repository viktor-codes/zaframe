# FR-05 — Booking and Order Lifecycle (P0)

> This step protects the dashboard from lying. Without lifecycle cleanup, pending bookings keep
> seats and dashboard counters can show fake demand, fake occupancy, and wrong availability.

## Problem

The product has async payment and guest booking flows. That creates real-world edge cases:

- user closes the tab before Stripe webhook arrives
- payment fails
- two users try to book the last seat
- pending bookings never expire
- guest booking/order becomes owned by a user after OTP verification

If lifecycle jobs and ownership policy are inconsistent, frontend metrics become unreliable.

## Goal

Make booking/order states truthful and stable enough for dashboard counts, customer account, and
manual testing through the frontend.

## Required Work

### TD-11 lifecycle cron

- [x] Productionize `run_booking_lifecycle`.
- [x] Expire stale pending bookings.
- [x] Expire pending course orders once all related bookings are no longer active.
- [x] Complete past confirmed bookings when the lifecycle rule says they are done.
- [x] Document how it runs locally and in production.
- [x] Add Makefile/script target if missing.

Implementation:

- Production runs Render cron `zeeframe-booking-lifecycle` from `render.yaml` every 5 minutes UTC.
- Local run: `make booking-lifecycle` or `cd backend && uv run python -m scripts.run_booking_lifecycle`.
- Lifecycle is idempotent. It expires `pending` bookings whose `reserved_until <= now`, clears their holds, expires pending orders without active bookings, and completes `confirmed` bookings only when `occurrence.end_time < now`.

### Dashboard metrics dependency

- [x] Explicitly document which dashboard widgets depend on lifecycle correctness:
  - today's participant count
  - free seats
  - pending vs paid bookings
  - owner booking count
  - revenue-like summaries
- [x] Ensure stale pending bookings do not keep capacity forever.
- [x] Ensure counts exclude expired/cancelled/refunded records where appropriate.

Dashboard dependency notes:

- Free seats and public/course availability count only `confirmed` bookings plus active pending holds (`pending` with `reserved_until > now`).
- Stale pending bookings are changed to `expired` by lifecycle and stop contributing to capacity.
- Owner/customer order lists include status so the frontend can separate `pending`, `paid`, `expired`, `cancelled`, and `refunded` records before showing revenue-like summaries.
- Revenue-like summaries must use `Payment` ledger rows and exclude `refunded`/`partially_refunded` amounts according to refund state, not raw pending orders.

### Payment state behavior

- [x] Define what happens when payment fails:
  - preferred: booking/order remains `pending_payment` until expiry
  - do not silently delete records without an audit trail
- [x] Define behavior for delayed Stripe webhook:
  - webhook can confirm booking/order after user leaves checkout
  - duplicate webhook is idempotent
- [x] Define behavior for expired pending booking then late payment webhook.

Payment behavior:

- Failed/unpaid Stripe checkout events are recorded in the payment ledger but do not confirm bookings/orders; the records remain `pending` until lifecycle expiry.
- Successful delayed webhook can confirm `pending` or `expired` bookings/orders after the user leaves checkout, but it rechecks capacity under occurrence locks first.
- If a late paid webhook arrives after expiry and the seat was taken, the booking becomes `cancelled` with `payment_status=overbooked_manual_review`; the related payment/order is marked `manual_review` so the owner/operator can refund/rebook manually.
- Paid webhooks for already `cancelled`/`refunded` orders are not silently accepted as normal success; they move the order/payment ledger to `manual_review`.
- Duplicate webhook delivery is skipped by `processed_webhook_events`.

### Last-seat concurrency

- [x] Add tests for two concurrent booking attempts for the last available seat.
- [x] Exactly one should succeed.
- [x] The loser receives a clear conflict/capacity error.
- [x] Avoid overbooking even under parallel requests.

### TD-03 ownership policy

- [x] Keep `identity.is_owned_by_user` as the single ownership policy for:
  - user-owned booking
  - user-owned order
  - guest booking/order attached after OTP
- [x] Do not duplicate guest/email ownership checks across booking/payment/order services.
- [x] Cover guest-to-user merge in tests.

### Orders visibility

- [x] Ensure course order status and related bookings remain consistent.
- [x] Support customer account views added in [FR-01](./fr-01-api-contract-gaps.md).
- [x] Support owner dashboard order views added in [FR-01](./fr-01-api-contract-gaps.md).

## Tests

- [x] Pending booking expires after configured TTL.
- [x] Expired booking releases capacity.
- [x] Confirmed past booking completes only according to explicit lifecycle rule.
- [x] Delayed webhook confirms pending booking/order.
- [x] Duplicate webhook does not duplicate side effects.
- [x] Late webhook after expiry follows a documented behavior.
- [x] Concurrent last-seat booking does not overbook.
- [x] Guest booking/order attaches to verified user and appears in account views.
- [x] Dashboard count endpoints ignore stale/expired records.

## Definition of Done

- [x] A manual dashboard test does not show stale pending bookings as real demand.
- [x] Capacity stays correct after failed/expired payments.
- [x] Ownership after guest-to-user merge is consistent across booking, order, and payment.
- [x] Lifecycle job has docs and tests.

## Out of Scope

- Full BI analytics dashboard.
- Subscription/credit lifecycle.
- Waitlist promotion after cancellation.
