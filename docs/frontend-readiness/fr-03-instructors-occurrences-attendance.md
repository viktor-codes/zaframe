# FR-03 — Instructors, Occurrences, and Attendance (P1)

> Depends on [FR-02](./fr-02-rbac-studio-members.md) if instructors are represented as
> `StudioMember` records.

## Problem

The dashboard needs to answer operational questions:

- Who teaches this class?
- Which classes are assigned to me as an instructor?
- Who attended?
- Who did not show up?

A bare `checked_in_at` field is not enough; the API and permissions must support the full
attendance workflow.

## Goal

Add instructor assignment and attendance actions that are idempotent, permission-checked, and
visible in owner/instructor dashboards.

## Domain Model

### Instructor

Recommended MVP model:

- [ ] Use `StudioMember.role = instructor`.
- [ ] Add `Occurrence.instructor_id` referencing `studio_members.id`.

Why: an instructor exists in the context of a studio. A user may be an instructor in one studio
and an owner/manager in another.

### Booking attendance

- [ ] Add or confirm:
  - `Booking.checked_in_at`
  - `Booking.no_show_at` or equivalent status if lifecycle statuses are implemented
- [ ] Prefer explicit lifecycle statuses if [FR-07](./fr-07-catalog-product-model.md) lands:
  - `confirmed`
  - `completed`
  - `no_show`
  - `cancelled`

## API Contract

- [ ] Allow owner/manager to assign `Occurrence.instructor_id`.
- [ ] Add `GET /occurrences/mine` or `GET /occurrences?instructor_id=me`.
- [ ] Include instructor display data in occurrence responses used by dashboard:
  - instructor user ID
  - instructor name
  - studio member role
- [ ] Add `PATCH /bookings/{booking_id}/check-in`.
- [ ] Add `PATCH /bookings/{booking_id}/mark-no-show`.
- [ ] Optional: add `PATCH /bookings/{booking_id}/undo-check-in` if manual correction is needed.

## Idempotency Rules

- [ ] Repeated check-in should not create duplicate side effects.
- [ ] Checking in an already checked-in booking returns the current booking state.
- [ ] Marking no-show after check-in should be rejected unless an explicit correction endpoint exists.
- [ ] Cancelled/refunded bookings cannot be checked in.

## Permission Rules

- [ ] Owner/manager can check in any booking in their studio.
- [ ] Instructor can check in bookings only for occurrences assigned to them.
- [ ] Non-member cannot view occurrence bookings.
- [ ] Customer cannot check themselves in unless a future self-check-in feature is explicitly added.

## Tests

- [ ] Owner assigns instructor to occurrence.
- [ ] Instructor sees assigned occurrences through `mine` endpoint/filter.
- [ ] Instructor cannot see another instructor's private dashboard list.
- [ ] Check-in is idempotent.
- [ ] No-show is idempotent.
- [ ] Cancelled booking cannot be checked in.
- [ ] Booking owner response includes `checked_in_at`, no-show state, and instructor display data where needed.

## Definition of Done

- [ ] Owner dashboard can show attendance for an occurrence.
- [ ] Instructor dashboard can show "my classes".
- [ ] Attendance actions are server-authorized and do not rely on frontend-only role checks.

## Out of Scope

- QR code check-in.
- Self check-in by customers.
- Payroll/compensation for instructors.
