# FR-02 — RBAC and Studio Members (P1)

> Do this after [FR-01](./fr-01-api-contract-gaps.md). This step replaces owner-only checks with
> explicit studio permissions while keeping the simple owner case working.

## Problem

The current authorization model is mostly `studio.owner_id == user.id`. That is enough for a solo
owner, but it breaks once the product needs managers, instructors, or staff dashboards.

Client-only checks such as `studio.owner_id !== user.id` are not enough; every permission must be
enforced on the backend.

## Goal

Add global user roles and per-studio membership roles without turning the app into a complex IAM
system.

## Domain Model

### `User.role`

- [ ] Add enum:
  - `user`
  - `studio_owner`
  - `admin`
- [ ] Default: `user`.
- [ ] Use for global platform-level permissions only.
- [ ] Do not use `User.role` to decide access to a specific studio.

### `StudioMember`

- [ ] Add model/table:
  - `id`
  - `studio_id`
  - `user_id`
  - `role`: `owner`, `manager`, `instructor`
  - `created_at`
  - `updated_at`
- [ ] Add unique constraint on `(studio_id, user_id)`.
- [ ] Add indexes:
  - `idx_studio_members_studio_id`
  - `idx_studio_members_user_id`
- [ ] When a studio is created, create an owner `StudioMember` for the creator.
- [ ] Keep `Studio.owner_id` during this phase for compatibility.

## Permission Contract

Add one backend permission layer:

- [ ] `require_studio_permission(studio_id, permission)` dependency or service helper.
- [ ] Supported permissions:
  - `view_dashboard`
  - `manage_studio`
  - `manage_services`
  - `manage_schedule`
  - `view_bookings`
  - `manage_bookings`
  - `check_in_booking`
  - `manage_members`
- [ ] Admin users may bypass studio membership only when explicitly intended.

## API Contract

- [ ] Expose roles to frontend through one of:
  - `GET /auth/me` -> `roles: [{ studio_id, role }]`
  - `GET /studios/my` -> each item includes `role`
- [ ] Add member management endpoints only if needed for the current UI:
  - `GET /studios/{studio_id}/members`
  - `POST /studios/{studio_id}/members`
  - `PATCH /studios/{studio_id}/members/{member_id}`
  - `DELETE /studios/{studio_id}/members/{member_id}`

## Ownership Policy Note

TD-03 (`identity.is_owned_by_user`) must remain the single shared helper for "mine" ownership
checks after guest bookings/orders are attached to a logged-in user. Do not duplicate ownership
logic inside booking, payment, or order endpoints.

## Migration Strategy

1. Add `User.role` and `StudioMember`.
2. Backfill one owner member for every existing studio.
3. Keep old `ensure_studio_owner` behavior working.
4. Introduce permission helpers.
5. Move endpoints from owner-only checks to permission checks incrementally.

## Tests

- [ ] Studio creator gets owner membership.
- [ ] Owner can manage studio, services, schedule, bookings, and members.
- [ ] Manager can manage configured areas but cannot manage members unless allowed.
- [ ] Instructor cannot manage studio settings.
- [ ] Non-member gets 403 or 404 according to existing anti-enumeration policy.
- [ ] `GET /auth/me` or `GET /studios/my` returns role data needed for navigation.

## Definition of Done

- [ ] All dashboard-relevant endpoints enforce permissions server-side.
- [ ] Frontend can render client/owner/instructor navigation without guessing from `owner_id`.
- [ ] Existing owner-only flows still pass.

## Out of Scope

- Complex custom permission matrix UI.
- Organization/team billing.
- AuditLog for permission changes — see [FR-11](./fr-11-future-backlog.md).
