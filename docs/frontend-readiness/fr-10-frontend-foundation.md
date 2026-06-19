# FR-10 — Frontend Foundation for Manual API Testing (P0)

> This step connects the backend readiness work to real UI flows. Do not rebuild what already
> exists in `lib/api`, `lib/auth`, dashboard, `/bookings`, or `/auth/me`; extend it.

## Problem

The backend has many usable endpoints, but the frontend needs stable clients, runtime validation,
error handling, and role-aware routing before the dashboard/account can scale.

## Goal

Make the frontend a reliable manual testing surface for backend APIs.

## API Clients

Add or extend typed clients for:

- [ ] auth/current user
- [ ] studios
- [ ] services
- [ ] schedule templates
- [ ] `POST /studios/{studio_id}/generate-occurrences`
- [ ] occurrences
- [ ] bookings owner/client
- [ ] orders customer/owner
- [ ] payments/refunds when [FR-04](./fr-04-stripe-connect-payments-refunds.md) lands
- [ ] Stripe Connect onboarding/status when [FR-04](./fr-04-stripe-connect-payments-refunds.md) lands

## Runtime Validation

- [ ] Add Zod schemas for API responses that the UI renders.
- [ ] Pay special attention to union shapes:
  - booking self vs owner response
  - booking created vs course booking response
  - studio list with/without services if old endpoint remains
- [ ] Infer TypeScript types from Zod schemas when schemas are frontend-specific.
- [ ] Prefer generated OpenAPI types for stable backend contracts when available.

## OpenAPI to TypeScript

- [ ] Decide whether to use OpenAPI-generated types or `packages/shared-types`.
- [ ] If OpenAPI generation is selected:
  - generate from `/openapi.json`
  - commit generated types only if project convention allows
  - document regeneration command
- [ ] Fix backend union endpoints before relying on generated types where possible.

## Error Handling

- [ ] Add global toast/notification layer.
- [ ] Parse Problem JSON consistently.
- [ ] Never show raw backend stack/error details to end users.
- [ ] Include `request_id` in developer-facing error details if backend exposes it.
- [ ] Handle auth lost / refresh failed with redirect or session reset.

## Idempotency Key

Client-side protection from double submit is separate from server-side capacity/concurrency tests.

- [ ] Generate an idempotency key for create booking.
- [ ] Generate an idempotency key for checkout session creation.
- [ ] Send it through an agreed header, for example `Idempotency-Key`.
- [ ] Disable submit buttons while request is in flight.
- [ ] Backend support must be added if it does not exist yet.
- [ ] Test browser double-click / retry behavior manually.

## Role-Aware Routing

- [ ] Keep basic auth guard.
- [ ] Add role-aware layouts:
  - customer account
  - owner dashboard
  - instructor/staff dashboard when FR-02/FR-03 land
- [ ] Do not infer permissions only from `owner_id` once RBAC exists.
- [ ] Use roles from `/auth/me` or `/studios/my`.

## Manual Test Screens

Minimum screens useful for backend testing:

- [ ] sign in / OTP verify
- [ ] current user account
- [ ] my bookings
- [ ] my orders
- [ ] owner studios
- [ ] studio services
- [ ] schedule templates / generate occurrences
- [ ] owner bookings
- [ ] occurrence bookings
- [ ] check-in/no-show after FR-03
- [ ] payout settings after FR-04

## Tests

- [ ] Vitest for `lib/api` request building and error parsing.
- [ ] Tests for Zod parsing of important API responses.
- [ ] Tests for auth refresh failure handling if practical.

## Definition of Done

- [ ] A developer can manually test core backend flows from the UI.
- [ ] API errors are visible and understandable.
- [ ] Double-submit does not create duplicate booking/checkout attempts when backend supports idempotency.
- [ ] Role-based navigation uses backend-provided access data.

## Out of Scope

- Pixel-perfect UI.
- Full Playwright suite.
- Marketing/public landing page polish.
