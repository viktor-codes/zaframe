# Frontend Readiness — Backend Work Plan

> Goal: prepare the backend, tests, logging, and frontend API foundation so studio dashboard
> and user account screens can be developed and manually tested without backend workarounds.

## Context

The project has already completed the modular monolith refactor. The next product step is not
"finish the backend"; it is to make the two critical journeys smooth:

1. Studio owner: sign in -> create studio -> publish storefront -> create services -> generate
   schedule -> connect payments -> receive bookings -> manage today's dashboard.
2. Customer: open studio page -> choose class/course -> book as guest or user -> pay -> see
   upcoming booking in the account -> cancel if policy allows.

Use this folder as a handoff pack for agents. Each `fr-*` file is intentionally scoped to one
logical, reviewable step.

## Already Done — Do Not Rebuild

- [x] `Booking.access_token` and `Order.access_token` exist via migration `006`; guest checkout works.
- [x] `Order.guest_phone` exists via migration `008`.
- [x] `Booking.payment_intent_id` exists from the initial schema and is written on payment confirm.
- [x] `GET /bookings/my` returns booking + occurrence + studio without N+1.
- [x] Base frontend `lib/api`, `lib/auth`, dashboard, `/bookings`, and `/auth/me` exist.
- [x] Modular monolith architecture is documented in `docs/adr/003-modular-monolith.md`.

## Phase 1 — Unblock MVP Frontend

- [ ] [FR-01: API Contract Gaps](./fr-01-api-contract-gaps.md)
  - `PATCH /auth/me` or `/users/me`
  - `GET /studios/my`
  - `GET /studios/{studio_id}/services`
  - Studio `slug`, `logo_url`, `cover_url`
  - customer and owner Orders API
- [ ] [FR-05: Booking and Order Lifecycle](./fr-05-booking-order-lifecycle.md)
  - TD-11 booking lifecycle cron
  - pending booking expiry
  - delayed Stripe webhook behavior
  - last-seat concurrency
  - TD-03 ownership policy stability after guest-to-user merge
- [ ] [FR-07: Catalog Product Model](./fr-07-catalog-product-model.md)
  - `Service.visibility`
  - occurrence cancellation behavior
  - schedule editing behavior contract
  - studio timezone contract
  - minimal cancellation policy
- [ ] [FR-10: Frontend Foundation](./fr-10-frontend-foundation.md)
  - API clients for services/schedule/generate/bookings/orders
  - Zod schemas for API responses
  - global errors/toasts
  - idempotency-key for create booking/checkout double-submit protection
  - OpenAPI -> TS types plan

## Phase 2 — Roles, Attendance, Payments

- [ ] [FR-02: RBAC and Studio Members](./fr-02-rbac-studio-members.md)
  - `User.role`
  - `StudioMember`
  - permission dependencies
  - roles in `/auth/me` or `/studios/my`
- [ ] [FR-03: Instructors and Attendance](./fr-03-instructors-occurrences-attendance.md)
  - instructor assignment
  - `GET /occurrences/mine`
  - check-in
  - no-show
- [ ] [FR-04: Stripe Connect, Payments, Refunds](./fr-04-stripe-connect-payments-refunds.md)
  - Stripe Connect onboarding/status
  - `Payment`
  - `Refund`
  - `Order.application_fee_cents`
  - `account.updated` webhook
- [ ] [FR-06: GDPR User Account](./fr-06-gdpr-user-account.md)
  - `User.marketing_consent`
  - `User.deleted_at`
  - delete account
  - export account data
  - deleted-user filtering

## Phase 3 — Engineering Quality

- [ ] [FR-08: Tests Structure](./fr-08-tests-structure.md)
  - move all backend tests under structured `backend/tests/`
  - group by architecture/unit/integration/e2e/factories
  - add critical behavior tests before frontend scale-up
- [ ] [FR-09: Logging and Observability](./fr-09-logging-observability.md)
  - structured logs
  - request context
  - domain events
  - PII/secrets policy
  - dashboard-friendly operational traces

## Future Backlog

- [ ] [FR-11: Future Backlog](./fr-11-future-backlog.md)
  - Waitlist
  - Room
  - AuditLog
  - subscriptions/credits
  - denormalized `Occurrence.booked_count`
  - optimistic version
  - reviews
  - notifications log
  - online classes
  - promo codes
  - galleries
  - booking sources

## Recommended Execution Order

1. `fr-01` + focused tests: unlock dashboard and account API contracts.
2. `fr-05`: make counts and pending states truthful before relying on dashboard metrics.
3. `fr-07`: lock product lifecycle contracts before the UI encodes assumptions.
4. `fr-10`: connect frontend clients, schemas, errors, and idempotency.
5. `fr-02` + `fr-03`: unlock staff/instructor dashboard.
6. `fr-04`: enable real payout/refund operations.
7. `fr-06`: complete account/privacy screens.
8. `fr-08` + `fr-09`: can run in parallel once the domain contracts stabilize.

## Definition of Done for This Pack

- [ ] Each implemented step has migration tests when it changes persistence.
- [ ] Each new or changed endpoint has integration tests.
- [ ] `/docs` exposes stable response schemas for generated frontend types.
- [ ] No raw ORM objects are returned from routers.
- [ ] Ownership and permissions are enforced server-side, not only in frontend code.
- [ ] Manual frontend testing can cover owner dashboard and customer account without Swagger-only flows.
