# Frontend Readiness — Backend Work Plan

> Goal: prepare the backend, tests, logging, and frontend API foundation so studio dashboard
> and user account screens can be developed and manually tested without backend workarounds.
>
> **Status snapshot (2026-07-27):** Phases 0–6 of the frontend ROADMAP are shipped. Index below
> marks FR items **done** only when the contract is live in code. Partial / deferred notes are
> explicit — do not treat unchecked future backlog as “blocked MVP”.

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

- [x] [FR-01: API Contract Gaps](./fr-01-api-contract-gaps.md)
  - `PATCH /auth/me`, `GET /studios/my`, `GET /studios/{id}/services`, slug/media, Orders API
- [x] [FR-05: Booking and Order Lifecycle](./fr-05-booking-order-lifecycle.md)
  - TD-11 cron, pending expiry, webhook-driven confirm, ownership after guest attach
  - Note: individual checkboxes inside the FR file may lag; behaviour is live
- [x] [FR-07: Catalog Product Model](./fr-07-catalog-product-model.md)
  - `Service.visibility`, occurrence cancel, schedule vs calendar, timezone, cancel policy
- [x] [FR-10: Frontend Foundation](./fr-10-frontend-foundation.md)
  - FSD clients, OpenAPI → TS (`npm run generate:api`), toasts, Idempotency-Key, role nav
  - Note: FR file checklists may still show open boxes; treat ROADMAP Phases 1–2 as source of truth

## Phase 2 — Roles, Attendance, Payments

- [x] [FR-02: RBAC and Studio Members](./fr-02-rbac-studio-members.md)
  - `User.role`, `StudioMember`, `require_studio_permission`, roles on `/auth/me` + `/studios/my`
  - Members CRUD: `GET/POST/PATCH/DELETE /studios/{id}/members` + Team UI (Wave 2)
- [x] [FR-03: Instructors and Attendance](./fr-03-instructors-occurrences-attendance.md)
  - instructor assignment, `GET /occurrences/mine`, check-in / no-show
- [~] [FR-04: Stripe Connect, Payments, Refunds](./fr-04-stripe-connect-payments-refunds.md)
  - **Shipped:** Connect onboarding/status, Payment ledger, payouts UI, `account.updated`
  - **Deferred:** live `application_fee` / platform take-rate writer (Wave 2.4 skipped unless asked)
- [x] [FR-06: GDPR User Account](./fr-06-gdpr-user-account.md)
  - `marketing_consent`, `deleted_at`, `POST /me/delete-account`, `GET /me/export` + UI/privacy pages

## Phase 1.5 — Stabilization (Blocking)

- [x] [FR-12: Stabilization Before Frontend](./fr-12-stabilization.md)
  - Quality gates restored; audit items closed or explicitly deferred in the FR file
  - Note: §11 historically said members API deferred — **superseded** by Wave 2 members endpoints

## Phase 3 — Engineering Quality

- [x] [FR-08: Tests Structure](./fr-08-tests-structure.md)
  - `backend/tests/{architecture,unit,integration,e2e}/` layout in use
- [x] [FR-09: Logging and Observability](./fr-09-logging-observability.md)
  - structlog, `request_id`, domain events, PII redaction policy, `/metrics`

## Future Backlog

- [ ] [FR-11: Future Backlog](./fr-11-future-backlog.md)
  - Waitlist, Room, AuditLog, subscriptions/credits, denormalized counts, reviews, etc.

## Recommended Execution Order

> Historical order for greenfield agents. Most Phase 1–3 items are **done** — prefer
> `frontend/docs/ROADMAP.md` Later (P2) and `docs/tech-debt/` for remaining work.

1. `fr-01` + focused tests: unlock dashboard and account API contracts. ✅
2. `fr-05`: make counts and pending states truthful. ✅
3. `fr-07`: lock product lifecycle contracts. ✅
4. `fr-10`: connect frontend clients, schemas, errors, and idempotency. ✅
5. `fr-02` + `fr-03`: unlock staff/instructor dashboard. ✅
6. `fr-04`: enable real payout/refund operations. ✅ (fee writer deferred)
7. `fr-06`: complete account/privacy screens. ✅
8. `fr-08` + `fr-09`: engineering quality. ✅

## Definition of Done for This Pack

- [x] Each implemented step has migration tests when it changes persistence.
- [x] Each new or changed endpoint has integration tests.
- [x] `/docs` exposes stable response schemas for generated frontend types.
- [x] No raw ORM objects are returned from routers.
- [x] Ownership and permissions are enforced server-side, not only in frontend code.
- [x] Manual frontend testing can cover owner dashboard and customer account without Swagger-only flows.
