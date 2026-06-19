# FR-09 — Logging and Observability (P1)

> Goal: make manual frontend testing and production debugging possible without leaking secrets or
> personal data.

## Problem

As soon as the frontend starts testing real flows, failures will span browser, API, database,
Stripe, and background lifecycle jobs. Plain logs without request context are not enough.

## Goal

Implement structured, contextual logging with a small set of domain events.

## Logging Standard

- [ ] Use `structlog` with JSON output in production.
- [ ] Use readable console output in development if already supported.
- [ ] Every log entry should include:
  - `timestamp`
  - `level`
  - `service`
  - `request_id`
- [ ] When available, include:
  - `user_id`
  - `studio_id`
  - `booking_id`
  - `order_id`
  - `payment_id`
  - `occurrence_id`
- [ ] Return `X-Request-ID` on every response.

## Request Middleware

- [ ] Generate request ID if client did not provide one.
- [ ] Bind request ID to log context.
- [ ] Log request start/end at an appropriate level.
- [ ] Log method, path, status code, duration.
- [ ] Do not log full request bodies by default.

## Error Logging

- [ ] Log unexpected exceptions with stack traces.
- [ ] Return safe RFC 7807 Problem JSON to clients.
- [ ] Do not expose internal exception details to frontend.
- [ ] Include `request_id` in error responses if project convention allows.

## PII and Secrets Policy

Never log:

- [ ] OTP codes
- [ ] JWT access tokens
- [ ] refresh tokens
- [ ] raw guest access tokens
- [ ] Stripe secrets
- [ ] full payment data
- [ ] passwords if password auth is ever added

Be careful with:

- [ ] email
- [ ] phone
- [ ] customer name

Prefer IDs and event names over raw personal data.

## Domain Events

Add focused logs for:

- [ ] OTP requested
- [ ] OTP verified
- [ ] user profile updated
- [ ] user account soft-deleted
- [ ] studio created/updated
- [ ] studio member added/role changed
- [ ] service created/visibility changed
- [ ] occurrence generated/cancelled
- [ ] booking created/cancelled/checked-in/no-show
- [ ] checkout session created
- [ ] payment confirmed via webhook
- [ ] refund created
- [ ] Stripe Connect onboarding started
- [ ] Stripe Connect account updated
- [ ] lifecycle job expired pending bookings

## Operational Dashboard Links

- [ ] Lifecycle job logs must include number of expired/completed bookings.
- [ ] Payment webhook logs must include Stripe event ID and idempotency outcome.
- [ ] Booking capacity conflict logs should be warning-level with occurrence ID.
- [ ] Permission denials should include user ID and target resource ID, but no PII.

## Tests

- [ ] Middleware adds `X-Request-ID`.
- [ ] Logs include request ID in request context.
- [ ] Error path logs exception and returns safe response.
- [ ] Sensitive values are not emitted in known auth/payment flows.

## Definition of Done

- [ ] A failed manual frontend flow can be traced by `request_id`.
- [ ] Stripe webhook processing can be traced by event ID.
- [ ] Lifecycle job effects are visible in logs.
- [ ] No secrets or tokens appear in logs.

## Out of Scope

- Datadog/Sentry integration.
- Metrics backend.
- Distributed tracing across multiple services.
