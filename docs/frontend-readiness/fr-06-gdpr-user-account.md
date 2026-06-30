# FR-06 — GDPR Minimum and User Account Privacy (P1)

> This step is needed before building full account settings and privacy screens.

## Problem

Adding database fields alone is not enough for privacy/account screens. The frontend needs
explicit endpoints and backend queries must consistently respect soft-deleted users.

## Goal

Implement a minimal privacy contract without overbuilding compliance tooling.

## User Fields

Add to `User`:

- [x] `marketing_consent`
- [x] `deleted_at`

Rules:

- [x] Default `marketing_consent` should be false unless explicitly collected.
- [x] `deleted_at` means soft-deleted user.
- [x] Soft-deleted users must not be able to authenticate.
- [x] Bookings, orders, and payments must remain for business/legal history.

Re-registration policy after soft delete: blocked for MVP. A deleted email remains tied to the
soft-deleted account so transactional history stays legally attributable. Re-registration with the
same email requires a future anonymization/support flow before this policy can change.

## API Contract

- [x] `PATCH /auth/me` can update:
  - `name`
  - `phone`
  - `marketing_consent`
- [x] `POST /me/delete-account`
  - sets `deleted_at`
  - revokes refresh tokens
  - clears auth cookies if called in browser flow
- [ ] `GET /me/export`
  - can be deferred, but document response shape if not implemented now

Deferred export response shape:

```json
{
  "user": {
    "id": 123,
    "email": "user@example.com",
    "name": "Ada Lovelace",
    "phone": "+353871234567",
    "marketing_consent": false,
    "created_at": "2026-06-20T00:00:00Z",
    "updated_at": "2026-06-20T00:00:00Z",
    "deleted_at": null
  },
  "bookings": [],
  "orders": [],
  "payments": []
}
```

## Deleted User Filtering

- [x] Auth lookup excludes deleted users.
- [x] User repository default read paths exclude deleted users where appropriate.
- [x] Admin/support paths may include deleted users only if explicitly named.
- [ ] Booking/order history should display anonymized or safe deleted-user data where needed.

## Tests

- [x] User can update marketing consent.
- [x] User can soft-delete account.
- [x] Soft-deleted user cannot refresh or log in.
- [x] Existing bookings/orders remain after soft delete.
- [x] Deleted user is filtered from normal user queries.
- [ ] Export endpoint returns expected user/account data if implemented.

## Definition of Done

- [x] Account settings screen can edit privacy fields.
- [x] Delete account flow is possible without losing transactional history.
- [x] Auth/session state is invalidated after deletion.

## Out of Scope

- Full legal GDPR automation.
- Hard deletion/anonymization job.
- Data-processing audit UI.
