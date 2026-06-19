# FR-07 — Catalog Product Model and Behavior Contracts (P0)

> This file exists to prevent frontend assumptions from becoming accidental business rules.
> Do this before the UI deeply encodes service, schedule, and occurrence behavior.

## Problem

The catalog is no longer just CRUD. It has product lifecycle states and behavior that must be
consistent across public storefront, owner dashboard, booking, payments, and account views.

## Goal

Make lifecycle states explicit and document how schedule changes, cancellations, media, timezone,
and cancellation policies behave.

## Service Visibility

Add `Service.visibility`:

- [ ] `draft`
- [ ] `published`
- [ ] `archived`

Rules:

- [ ] Public storefront/search shows only `published`.
- [ ] Owner dashboard can see all service states.
- [ ] Archived services are not bookable.
- [ ] Avoid using `is_active` as the only product lifecycle field.

## Occurrence to Service Link

- [ ] Confirm `Occurrence.service_id` exists and is required for bookable classes/courses.
- [ ] If missing or optional in the wrong places, add/normalize it.
- [ ] Dashboard-created sessions must not become "bare" occurrences disconnected from services.
- [ ] Course availability must be based on the same service-occurrence relationship.

## Occurrence Lifecycle

Define explicit occurrence statuses:

- [ ] `scheduled`
- [ ] `cancelled`
- [ ] `completed`

Add cancellation metadata:

- [ ] `cancelled_at`
- [ ] `cancellation_reason`

Rules:

- [ ] Cancelling an occurrence must not delete it.
- [ ] Existing customer account entries should show cancelled state.
- [ ] Owner dashboard should preserve history.
- [ ] Deleting an occurrence with bookings should be forbidden or converted into cancellation.

## Schedule Editing Behavior Contract

This is a behavioral contract, not just an API detail.

- [ ] Define and document the rule for editing schedule templates.
- [ ] Recommended MVP rule:
  - changes affect only future occurrences that have not been generated yet
  - already generated occurrences are not mutated automatically
  - owner must edit/cancel generated occurrences explicitly
- [ ] Add tests proving generated occurrences do not silently change after template edits.
- [ ] Expose enough copy/metadata for frontend to warn owners.

## Studio Timezone Contract

Studio timezone directly affects occurrence generation and daylight saving behavior.

- [ ] Confirm `Studio.timezone` is required at onboarding.
- [ ] Store IANA timezone strings only.
- [ ] Generate occurrences relative to the studio timezone.
- [ ] Return API datetimes consistently according to the existing datetime ADR.
- [ ] Test DST-sensitive generation around timezone transitions.

## Cancellation Policy

Add minimal policy to `Studio`:

- [ ] `cancel_before_hours`

Rules:

- [ ] Customer can cancel only before the configured cutoff.
- [ ] Owner/manager may bypass if product rules allow.
- [ ] Frontend can show "Cancellation available until ...".

## Media and Branding

Minimum fields:

- [ ] `logo_url`
- [ ] `cover_url`

Future:

- [ ] gallery media model — see [FR-11](./fr-11-future-backlog.md).

Rules:

- [ ] URL fields are acceptable before S3/R2 upload pipeline exists.
- [ ] Do not hardcode storage provider details in domain services.

## Tests

- [ ] Draft service is hidden from public storefront/search.
- [ ] Published service is visible and bookable.
- [ ] Archived service is hidden/unbookable but preserved.
- [ ] Occurrence cancellation preserves customer history.
- [ ] Occurrence with bookings cannot be hard-deleted.
- [ ] Schedule template edit does not silently mutate existing generated occurrences.
- [ ] Timezone validation rejects invalid timezone strings.
- [ ] Occurrence generation uses studio timezone.
- [ ] Cancellation cutoff prevents late customer cancellation.

## Definition of Done

- [ ] Product lifecycle is explicit in models and schemas.
- [ ] Frontend can safely display draft/published/archived services.
- [ ] Owner dashboard can explain schedule edit consequences.
- [ ] Customer account can show cancelled/completed/upcoming states correctly.

## Out of Scope

- Complex recurring schedule diff engine.
- Notification dispatch for cancellations.
- Media upload service implementation.
