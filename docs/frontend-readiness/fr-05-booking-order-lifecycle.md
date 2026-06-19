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

- [ ] Productionize `run_booking_lifecycle`.
- [ ] Expire stale pending bookings.
- [ ] Complete past confirmed bookings when the lifecycle rule says they are done.
- [ ] Document how it runs locally and in production.
- [ ] Add Makefile/script target if missing.

### Dashboard metrics dependency

- [ ] Explicitly document which dashboard widgets depend on lifecycle correctness:
  - today's participant count
  - free seats
  - pending vs paid bookings
  - owner booking count
  - revenue-like summaries
- [ ] Ensure stale pending bookings do not keep capacity forever.
- [ ] Ensure counts exclude expired/cancelled/refunded records where appropriate.

### Payment state behavior

- [ ] Define what happens when payment fails:
  - preferred: booking/order remains `pending_payment` until expiry
  - do not silently delete records without an audit trail
- [ ] Define behavior for delayed Stripe webhook:
  - webhook can confirm booking/order after user leaves checkout
  - duplicate webhook is idempotent
- [ ] Define behavior for expired pending booking then late payment webhook.

### Last-seat concurrency

- [ ] Add tests for two concurrent booking attempts for the last available seat.
- [ ] Exactly one should succeed.
- [ ] The loser receives a clear conflict/capacity error.
- [ ] Avoid overbooking even under parallel requests.

### TD-03 ownership policy

- [ ] Keep `identity.is_owned_by_user` as the single ownership policy for:
  - user-owned booking
  - user-owned order
  - guest booking/order attached after OTP
- [ ] Do not duplicate guest/email ownership checks across booking/payment/order services.
- [ ] Cover guest-to-user merge in tests.

### Orders visibility

- [ ] Ensure course order status and related bookings remain consistent.
- [ ] Support customer account views added in [FR-01](./fr-01-api-contract-gaps.md).
- [ ] Support owner dashboard order views added in [FR-01](./fr-01-api-contract-gaps.md).

## Tests

- [ ] Pending booking expires after configured TTL.
- [ ] Expired booking releases capacity.
- [ ] Confirmed past booking completes only according to explicit lifecycle rule.
- [ ] Delayed webhook confirms pending booking/order.
- [ ] Duplicate webhook does not duplicate side effects.
- [ ] Late webhook after expiry follows a documented behavior.
- [ ] Concurrent last-seat booking does not overbook.
- [ ] Guest booking/order attaches to verified user and appears in account views.
- [ ] Dashboard count endpoints ignore stale/expired records.

## Definition of Done

- [ ] A manual dashboard test does not show stale pending bookings as real demand.
- [ ] Capacity stays correct after failed/expired payments.
- [ ] Ownership after guest-to-user merge is consistent across booking, order, and payment.
- [ ] Lifecycle job has docs and tests.

## Out of Scope

- Full BI analytics dashboard.
- Subscription/credit lifecycle.
- Waitlist promotion after cancellation.
