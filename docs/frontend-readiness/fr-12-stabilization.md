# FR-12 — Stabilization Before Frontend (P0)

> This step restores the project's green-gate discipline before any frontend work in FR-10.
> It is mostly "make tests catch up with code", not new feature work. Do NOT start FR-10 until
> the gates below are green.
>
> Source: backend audit on 2026-06-20 (after FR-01..FR-09, excluding FR-10/FR-11).

## Quality Gates — Current State

Run from `backend/`:

```bash
uv run --group dev pytest -q        # RED: 13 failed, 208 passed
uv run --group dev ruff check .     # GREEN
uv run --group dev lint-imports     # RED: 1 broken contract
uv run --group dev pyright          # RED: 1076 errors (app: 1, scripts: 5, tests: 1070)
```

Definition of Done for FR-12: all four gates GREEN.

---

## Critical — Red Quality Gates

### 1. Fix the 13 failing tests

Two root causes, both are tests lagging behind shipped code.

- [x] **Mock drift (Stripe Connect).** Production now calls
      `uow.bookings.get_by_id_with_occurrence_and_studio(...)`, but tests still mock
      `get_by_id_with_occurrence`, returning a `MagicMock` that fails on `await`.
  - File: `backend/app/modules/payment/checkout.py:56`
  - Failing: `tests/integration/api/test_guest_checkout_access_token.py` (5 tests)
  - Fix: update mocks to the new method name with `AsyncMock`.
- [x] **`occurrences.service_id` is now NOT NULL (FR-07).** Several tests build occurrences
      without `service_id` and hit `NotNullViolationError`.
  - Failing: `test_api_auth.py::test_delete_account_*`, `test_booking_duplicate.py::test_rebook_after_cancel_succeeds`,
    `test_bookings_authz.py::test_guest_can_view_and_cancel_own_booking`,
    `test_overbooking_confirm.py` (3 tests), `test_payment_confirm_queries.py` (2 tests)
  - Fix: give occurrence factories/builders a required `service_id` (create a service first).
- [x] **Verify safety tests actually assert again.** The overbooking, idempotency, and
      payment-confirm-query-count tests currently error before their assertions. After the fix,
      confirm they pass on their real logic, not just stop erroring.
  - Verified: FR-12 targeted safety tests pass (`36 passed`), and full backend pytest passes
    (`229 passed`).

### 2. Fix the broken architecture contract

- [x] `payment.router` imports `catalog.studio`, violating the import-linter contract
      "payment only reaches booking and identity (not catalog/auth)".
  - File: `backend/app/modules/payment/router.py:19`
    (`from app.modules.catalog.studio import require_studio_permission`)
  - Fix options (pick one, document choice):
    - promote `require_studio_permission` into a shared layer (e.g. `identity` or `core`),
    - or expose a payment-owned permission helper that does not import `catalog`.
  - Decision: expose a payment-owned `require_studio_payout_permission` helper in
    `backend/app/modules/payment/access.py`. Payment endpoints only need the
    `manage_payouts` permission, so this keeps the import contract narrow without moving
    the catalog-owned generic studio RBAC helper.
  - Re-run `uv run --group dev lint-imports` -> all contracts KEPT.

### 3. Make `tests/` pass pyright strict

- [x] 1070 of 1076 pyright errors are in `tests/` (untyped mocks, `reportUnknownMemberType`,
      Stripe TypedDict access in assertions).
- [x] Decide and apply one consistent approach:
  - type the test helpers/mocks and fixtures, or
  - explicitly scope strict checking (adjust `pyright` `include`/`exclude` in `pyproject.toml`)
    as a documented, intentional decision rather than silent drift.
- Decision: scope strict `pyright` to `app/` and `scripts/` for FR-12. `tests/` remain covered
  by `pytest`; typing fixtures/mocks is deferred as explicit test-typing debt instead of
  blocking frontend readiness on 1000+ test-only diagnostics.
- [x] Fix the single real `app/` error:
      `backend/app/modules/catalog/service/schemas.py:131` — `visibility` overrides a field
      without a default value.
- [x] Goal: `uv run --group dev pyright` reports 0 errors under the chosen policy.

### 4. Fix seed/simulation scripts

- [x] E2E seed/simulation modules failed because they lagged the schema (missing required args).
  - `tests/e2e/e2e_seed.py:57` missing `cancel_before_hours`; `:79` missing `instructor_id`.
  - `tests/e2e/seed_and_simulate.py:107` missing `cancel_before_hours`; `:166` missing `instructor_id`;
    `:205` dead comparison (`int` vs `None`).
- [x] After fix, both modules run end-to-end against a local DB.
  - Verified: `uv run python -m tests.e2e.seed_and_simulate` and
    `uv run python -m tests.e2e.e2e_seed` both complete.

---

## Critical — Production / Auth / Payments

### 5. OTP delivery must not silently succeed

- [x] In production (`DEBUG=False`) without `RESEND_API_KEY`, `send_otp_email` returns `False`
      but the router still returns `OTPSentResponse`.
  - Files: `backend/app/modules/auth/service.py:74-90`, `backend/app/modules/auth/router.py:108-114`,
    `backend/app/integrations/email/service.py:36-46`
  - Fix: if delivery is not accepted in production, fail the OTP request with a clear error
    instead of reporting success.
- [x] Move the hardcoded sender out of code into config.
  - File: `backend/app/integrations/email/service.py:54` (`onboarding@resend.dev`)
  - Add a setting (e.g. `EMAIL_FROM`) and reference `.env.example`.

### 6. Never log OTP codes

- [x] `DEBUG=True` logs the raw OTP via a direct `logger.info(..., otp_code=code)` bypassing
      `safe_log_fields`.
  - File: `backend/app/integrations/email/service.py:38-42`
  - Fix: remove the code from logs, or route through `safe_log_fields` so it is redacted.

### 7. Stripe Connect fee / currency must be real or explicitly deferred

- [x] When a studio's Connect onboarding is incomplete, checkout is created without
      `transfer_data`, so funds go to the platform account silently.
  - File: `backend/app/modules/payment/checkout.py:80-85`
- [x] `Order.application_fee_cents` is read at checkout but never set at order creation.
  - File: `backend/app/modules/booking/order/service.py:108-120`
- [x] Order currency is hardcoded `"eur"` instead of `settings.STRIPE_CURRENCY`.
  - File: `backend/app/modules/booking/order/service.py:117`
- [x] Decision required: either implement platform fee + destination charges end-to-end, or
      explicitly gate paid checkout behind completed Connect onboarding and document the deferral.
  - Decision: paid checkout is gated behind Connect readiness; platform fee remains explicitly
    deferred until fee calculation is implemented end-to-end.

---

## Major — Access Control Leaks

### 8. Draft/archived services are publicly reachable by ID

- [x] `is_publicly_visible()` exists on the model but is not enforced on these endpoints:
  - `GET /services/{service_id}` — `backend/app/modules/catalog/service/router.py:70-77`
  - `GET /services/{service_id}/availability` — same file, ~80-97
  - `GET /services/{service_id}/schedule-templates` — same file, ~143-154 (leaks draft schedules)
  - Model helper: `backend/app/models/service.py:176-182`
- [x] Fix: public reads return only published+active services; owner/manager can see all states
      via authenticated access.

### 9. Unauthenticated list endpoints expose data

- [x] `GET /occurrences` has no auth and lets anyone enumerate slots by studio/instructor/status.
  - File: `backend/app/modules/catalog/occurrence/router.py:42-64`
- [x] `GET /studios?owner_id=` is public and lets anyone enumerate a studio owner's studios.
  - File: `backend/app/modules/catalog/studio/router.py:44-68`
- [x] Fix: scope these to authenticated/authorized access, or strip owner-only filters from
      public variants (align with `GET /studios/my`).

### 10. Orders permission check is conditional

- [x] `GET /orders` only checks permission when `studio_id` is explicitly provided; without it,
      a studio member with `view_bookings` can see orders across all their studios.
  - File: `backend/app/modules/booking/order/router.py:33-57`
- [x] Fix: always enforce per-studio permission, or require `studio_id`.

### 11. RBAC `manage_members` has no API

- [x] Permission is declared but there are no invite/update/remove member endpoints.
  - File: `backend/app/modules/catalog/studio/service.py:35-47`
- [x] Fix: add minimal member management endpoints (or explicitly defer if no screen needs it yet
      per the FR-11 promotion rule).
  - Decision (FR-12 era): deferred until UI needed.
  - **Update (Wave 2, 2026-07):** members list/manage API + Team UI shipped
    (`/studios/{id}/members`, `features/manage-members`).

---

## Minor

- [x] Rate limiting is in-memory unless `REDIS_URL` is set; multiple instances bypass OTP/checkout
      limits. Document Redis as required for multi-instance prod.
  - File: `backend/app/core/rate_limit.py:16-20`
- [x] `GET /health` returns hardcoded `"version": "1.0.0"` instead of `settings.APP_VERSION`.
  - File: `backend/app/api/health.py:31`
- [x] Unmatched webhook events return 200 without recording, losing some Connect status updates.
  - File: `backend/app/modules/payment/webhook_processor.py:119-125, 286-291`
- [x] Files over the 150-line rule (≤200 acceptable as a soft gate for now): `webhook_processor.py` (317),
      `payment/router.py` (278), `catalog/studio/service.py` (272), `auth/service.py` (220), `main.py` (217),
      `booking/router.py` (208), `catalog/service/router.py` (203), `booking/service.py` (201).
  - Decision: tracked as refactor debt; splitting all large files remains out of scope for FR-12.
- [x] Default `DATABASE_URL` points to local postgres with `postgres:postgres`; ensure prod always
      overrides it. File: `backend/app/core/config.py:29-31`.
- [x] Decide re-registration policy after GDPR soft delete (same email is currently blocked forever).
  - Files: `backend/app/modules/auth/service.py:50-58`, `backend/app/modules/identity/service.py:43-47`
  - Decision: same-email re-registration remains blocked for MVP until anonymization/support flow
    is designed.

---

## Recommended Order

1. Section 1 (tests green) — unblocks trust and re-enables safety tests.
2. Section 2 (import contract) — small, removes architecture drift.
3. Section 4 (seed scripts) — needed for manual testing.
4. Section 3 (pyright policy) — make the gate honest.
5. Sections 5-7 (auth/payments prod blockers).
6. Sections 8-10 (access-control leaks).
7. Section 11 + Minor as capacity allows.

## Definition of Done

```bash
cd backend
uv run --group dev pytest -q        # all pass
uv run --group dev ruff check .     # clean
uv run --group dev lint-imports     # all contracts KEPT
uv run --group dev pyright          # 0 errors under documented policy
uv run python -m tests.e2e.seed_and_simulate # runs end-to-end
```

- [x] All four gates green.
- [x] Safety tests (overbooking, webhook idempotency, payment query counts) pass on real logic.
- [x] No OTP codes or secrets in logs; OTP request fails honestly when undeliverable in prod.
- [x] No draft/archived service data or owner enumeration without authorization.
- [x] Platform fee/currency behavior is either implemented or explicitly, documentedly deferred.

## Out of Scope

- FR-10 frontend foundation work.
- New product features from FR-11 backlog.
- Splitting all >150-line files (track separately as refactor debt unless trivial).
