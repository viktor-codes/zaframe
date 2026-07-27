# ZeeFrame — CONTRACTS (Frontend ↔ Backend)

> Source of truth for the frontend. If the backend changes a contract, this file changes first.
> Verified against backend code on 2026-07-05. Base URL: `/api/v1`.

## 1. Roles

### Global roles (`UserRole`, `backend/app/models/user.py`)

| Role | Meaning |
|------|---------|
| `user` | Customer: account, own bookings/orders |
| `studio_owner` | Can create studios; staff access comes from `StudioMember`, not this flag |
| `admin` | Everything (admin bypass on selected endpoints) |

### Studio roles (`StudioMemberRole`) and how the frontend learns them

`GET /auth/me` → `CurrentUserResponse` includes:

```json
{ "...user fields": "...", "roles": [{ "studio_id": 1, "role": "owner" }] }
```

`GET /studios/my` → `StudioWithRoleResponse[]` (each studio + current user's `role`).
Frontend builds navigation, guards, and the StudioSwitcher from these two responses.

## 2. Permissions matrix (mirror of `STUDIO_PERMISSIONS_BY_ROLE`)

| Permission | owner | manager | instructor |
|--------------------|:-----:|:-------:|:----------:|
| `view_dashboard` | ✅ | ✅ | ✅ |
| `manage_studio` | ✅ | — | — |
| `manage_services` | ✅ | ✅ | — |
| `manage_schedule` | ✅ | ✅ | — |
| `view_bookings` | ✅ | ✅ | ✅ |
| `manage_bookings` | ✅ | ✅ | — |
| `check_in_booking` | ✅ | ✅ | ✅ |
| `manage_payouts` | ✅ | ✅ | — |
| `manage_members` | ✅ | — | — |

The frontend copy of this matrix lives in `shared/lib/constants.ts` and feeds
`usePermission()`. Enforcement is server-side; the frontend gate is UX only.

## 3. Entity statuses (from models — the full sets, wider than early brainstorms)

```text
Booking:    pending → confirmed → completed
                    ↘ cancelled | expired | no_show
Order:      pending → paid → refunded
                    ↘ cancelled | expired | manual_review
Occurrence: scheduled → completed | cancelled
Service.visibility: draft → published → archived
```

UI notes:

- `pending` booking/order = unpaid hold → show timer + "Complete payment".
- `expired` = payment window passed → offer rebooking.
- `manual_review` (order) = webhook anomaly → "Payment is being verified, contact support".
- Storefront queries only see `published` services and `scheduled` occurrences.
- Never compare raw strings in components — use constants from `shared/lib/constants.ts`.

## 4. Error format — RFC 7807 Problem JSON (implemented in `backend/app/main.py`)

```json
{
  "type": "app-error:ConflictError",
  "title": "Conflict",
  "status": 409,
  "detail": "human-readable message",
  "request_id": "uuid"
}
```

- `X-Request-ID` header is present on every response, including errors — attach it to logs.
- Status semantics: 400 business-rule violation (`ValidationError`), 401 unauthenticated,
  403 no permission, 404 not found / foreign resource, 409 state conflict,
  422 Pydantic validation (FastAPI `detail` is an **array** of field errors), 429 rate limit,
  503 upstream unavailable (e.g. Stripe not configured).
- **No machine-readable business code yet** (`BOOKING_CONFLICT` etc.). MVP maps errors by
  `status` + context of the call. Adding a `code` field is in the backend backlog.

## 5. Pagination — envelope (shipped 2026-07-05)

All list endpoints return a uniform envelope with `page` / `size` query params
(1-based page, default `size=20`, max `100`):

```json
{ "items": [], "total": 120, "page": 1, "size": 20 }
```

Legacy `/count` endpoints and `skip` / `limit` query params are removed.
`GET /search` still returns a plain array until search pagination is added.

## 6. Key endpoints by surface

### Auth (all surfaces)

| Endpoint | Notes |
|----------|-------|
| `POST /auth/otp/request` | email → OTP |
| `POST /auth/otp/verify` | → tokens + user |
| `POST /auth/refresh` | refresh access token |
| `POST /auth/logout` | 204 |
| `GET /auth/me` | user + studio roles (see §1) |
| `PATCH /auth/me` | profile update (name, phone, marketing consent) |

### Storefront (public, no auth)

| Endpoint | Notes |
|----------|-------|
| `GET /studios/slug/{slug}/public` | `StudioPublicResponse`: profile + `PublicService[]` (published only, availability, term info) |
| `GET /studios` | catalog list |
| `GET /search` | studio search |
| `GET /services/{id}/availability` | course availability / overbooked dates |
| `GET /occurrences?service_id=…` | bookable slots |
| `POST /bookings` | guest or user (optional Bearer); `BookingCreate` (single) or `CourseBookingCreate` (course → Order + N bookings); with Bearer → `user_id` set immediately; without → guest until OTP attach; returns `access_token` for checkout; rate limit 10/min |
| `POST /payments/checkout-session` | Stripe Checkout for single booking; **requires** `Idempotency-Key` header |
| `POST /payments/order-checkout-session` | Stripe Checkout for course order; **requires** `Idempotency-Key` |

Guest flow: `access_token` from booking/order is kept in `sessionStorage` after create.
Deep links use `/bookings/{id}/confirm#access_token=…` (hash is not sent to servers;
legacy `?access_token=` is still accepted once and stripped). After OTP sign-in, guest
bookings merge by email (`include_guest_email=true` on `/bookings/my`).

### Account (customer, auth required)

| Endpoint | Notes |
|----------|-------|
| `GET /bookings/my` | booking + occurrence + studio nested (no N+1) |
| `GET /bookings/{id}` | self or owner perspective |
| `PATCH /bookings/{id}/cancel` | respects `cancel_before_hours` cutoff |
| `GET /orders/my` | orders + service + booking summaries |
| `GET /orders/{id}` | session owner **or** guest `access_token` as Bearer (same gate as order checkout); nested bookings include `reserved_until`; no secrets / Stripe ids |

### Dashboard (studio staff, auth + studio permission)

| Endpoint | Permission | Notes |
|----------|------------|-------|
| `GET /studios/my` | any member | studios + my role |
| `POST /studios` / `PATCH /studios/{id}` / `DELETE /studios/{id}` | owner (`manage_studio`) | |
| `GET /studios/{id}/services` | member | includes drafts |
| `POST /services` / `PATCH /services/{id}` / `DELETE /services/{id}` | `manage_services` | `visibility` field drives draft/publish/archive |
| `GET /services/{id}/schedule-templates` + POST/PATCH/DELETE `/services/schedule-templates/{id}` | `manage_schedule` | template edits never touch existing occurrences |
| `POST /studios/{id}/generate-occurrences` | `manage_schedule` | days + start_time + weeks_count |
| `GET /studios/{id}/occurrences` | member | filters: date range, status; includes `confirmed_count` / `pending_count` |
| `POST /occurrences` / `PATCH /occurrences/{id}` / `DELETE /occurrences/{id}` | `manage_schedule` | calendar mode |
| `GET /occurrences/mine` | instructor | "my sessions" |
| `GET /bookings` | `view_bookings` | filter: `studio_id` (recommended), occurrence, status; nested `occurrence` |
| `PATCH /bookings/{id}/check-in` | `check_in_booking` | |
| `PATCH /bookings/{id}/mark-no-show` | `check_in_booking` | |
| `GET /orders` | owner | studio orders |
| `GET /studios/{id}/payments` | `manage_payouts` | payment list (P1) |

### Webhooks (backend-internal, listed for awareness)

`POST /webhooks/stripe` — payment confirmation is asynchronous; the success page must poll
booking status (`GET /bookings/{id}`) or order status (`GET /orders/{id}`) instead of
assuming instant confirmation. Guest order poll uses the create `access_token` until
webhook clears it; after clear, session owner / email match still works.

## 7. Known contract gaps (tracked, do not build around silently)

| Gap | Owner | Status |
|-----|-------|--------|
| Pagination envelope `{items, total, page, size}` | backend | **done** — all paginated list endpoints |
| Machine-readable error `code` | backend | backlog (post-MVP) |
| FR-12 stabilization (failing tests, auth/payment prod blockers) | backend | **done** — see `docs/frontend-readiness/fr-12-stabilization.md` |
| `GET /orders/{id}` for course success-page poll | backend | **done** — guest Bearer token or session owner; see Account table |
