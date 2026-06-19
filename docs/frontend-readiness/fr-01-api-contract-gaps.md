# FR-01 — API Contract Gaps Before Frontend (P0)

> Read [README.md](./README.md). This step unlocks the first useful owner dashboard and
> user account screens without introducing RBAC or Stripe Connect yet.

## Problem

The backend has the core domain flows, but several frontend-critical contracts are missing or
awkward:

| Gap | Impact |
|-----|--------|
| No `PATCH /auth/me` or `/users/me` | User account settings cannot edit name/phone/consent. |
| No `GET /studios/my` | Owner dashboard relies on public `owner_id` filtering. |
| No `GET /studios/{studio_id}/services` | Owner cannot list services for CRUD without search/public workarounds. |
| Studio CRUD response does not expose `slug` | Dashboard cannot show/manage public URL. |
| Studio media is incomplete | Public page/card onboarding needs at least logo and cover. |
| No Orders API | Customer account cannot show course purchases as `Order + N bookings`. |

## Goal

Add stable, typed API contracts for dashboard/account MVP while keeping existing routes backward
compatible.

## Required Backend Changes

### Identity / current user

- [ ] Add `PATCH /auth/me` or `PATCH /users/me`.
- [ ] Accept only editable profile fields:
  - `name`
  - `phone`
  - `marketing_consent` only if FR-06 is implemented in the same pass
- [ ] Return `UserResponse`.
- [ ] Do not allow changing `email`, `role`, `deleted_at`, or server-managed fields.

### Studios

- [ ] Add `GET /studios/my`.
- [ ] Scope result to the authenticated user.
- [ ] Return a typed list, not a shape-changing union.
- [ ] Include each studio's role if FR-02 is already implemented; otherwise owner-only is fine.
- [ ] Add `slug` to `StudioCreate`, `StudioUpdate`, and `StudioResponse` if the model already has it.
- [ ] Add minimal media fields:
  - `logo_url`
  - `cover_url`
- [ ] Validate `slug` uniqueness and safe URL format.
- [ ] Keep existing `GET /studios?owner_id=` for compatibility, but do not use it for dashboard.

### Services by studio

- [ ] Add `GET /studios/{studio_id}/services`.
- [ ] Public read is acceptable only if it mirrors current service visibility rules.
- [ ] For owner dashboard, enforce authenticated access when draft/archived services are included.
- [ ] Support pagination if the project pattern requires list endpoints to be paginated.
- [ ] Return `list[ServiceResponse]`.

### Orders

- [ ] Add `GET /orders/my`.
- [ ] Add owner-facing order list, either:
  - `GET /orders` scoped to current user's studios, or
  - `GET /studios/{studio_id}/orders`.
- [ ] Include enough data for account/dashboard:
  - order status
  - total amount
  - guest/user contact display fields
  - related service
  - related booking IDs or nested booking summaries
  - payment status if `Payment` model exists

## Tests

- [ ] `PATCH /auth/me` edits allowed fields and rejects protected fields.
- [ ] `GET /studios/my` returns only current user's studios.
- [ ] `GET /studios/{studio_id}/services` returns dashboard-usable service list.
- [ ] Non-owner cannot access draft/archived service views if service visibility exists.
- [ ] Studio slug uniqueness conflict returns 409.
- [ ] Orders API returns only current user's orders or current owner's studio orders.

## Definition of Done

```bash
cd backend
uv run pytest tests/integration -q
uv run ruff check .
uv run pyright
```

- [ ] OpenAPI has explicit response models for all new endpoints.
- [ ] Frontend can build owner studio list, service CRUD list, account profile form, and course order list without API workarounds.

## Out of Scope

- Full RBAC (`StudioMember`) — see [FR-02](./fr-02-rbac-studio-members.md).
- Stripe Connect payouts — see [FR-04](./fr-04-stripe-connect-payments-refunds.md).
- Full media upload pipeline; URL fields are acceptable for this step.
