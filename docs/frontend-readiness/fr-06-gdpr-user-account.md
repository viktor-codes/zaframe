# FR-06 — GDPR Minimum and User Account Privacy (P1)

> This step is needed before building full account settings and privacy screens.

## Problem

Adding database fields alone is not enough for privacy/account screens. The frontend needs
explicit endpoints and backend queries must consistently respect soft-deleted users.

## Goal

Implement a minimal privacy contract without overbuilding compliance tooling.

## User Fields

Add to `User`:

- [ ] `marketing_consent`
- [ ] `deleted_at`

Rules:

- [ ] Default `marketing_consent` should be false unless explicitly collected.
- [ ] `deleted_at` means soft-deleted user.
- [ ] Soft-deleted users must not be able to authenticate.
- [ ] Bookings, orders, and payments must remain for business/legal history.

## API Contract

- [ ] `PATCH /auth/me` or `/users/me` can update:
  - `name`
  - `phone`
  - `marketing_consent`
- [ ] `POST /me/delete-account`
  - sets `deleted_at`
  - revokes refresh tokens
  - clears auth cookies if called in browser flow
- [ ] `GET /me/export`
  - can be deferred, but document response shape if not implemented now

## Deleted User Filtering

- [ ] Auth lookup excludes deleted users.
- [ ] User repository default read paths exclude deleted users where appropriate.
- [ ] Admin/support paths may include deleted users only if explicitly named.
- [ ] Booking/order history should display anonymized or safe deleted-user data where needed.

## Tests

- [ ] User can update marketing consent.
- [ ] User can soft-delete account.
- [ ] Soft-deleted user cannot refresh or log in.
- [ ] Existing bookings/orders remain after soft delete.
- [ ] Deleted user is filtered from normal user queries.
- [ ] Export endpoint returns expected user/account data if implemented.

## Definition of Done

- [ ] Account settings screen can edit privacy fields.
- [ ] Delete account flow is possible without losing transactional history.
- [ ] Auth/session state is invalidated after deletion.

## Out of Scope

- Full legal GDPR automation.
- Hard deletion/anonymization job.
- Data-processing audit UI.
