# FR-08 — Backend Tests Structure (P1)

> Goal: all backend tests must live under `backend/tests/` with a clear structure by test level
> and domain. This step is allowed to move tests, but must not silently change behavior.

## Problem

Tests exist and are valuable, but they should be grouped consistently before the project grows
further. A mature structure makes it obvious where to add new coverage and what each test level
is allowed to touch.

## Target Layout

```
backend/tests/
├── architecture/
│   ├── test_import_contracts.py
│   └── test_module_boundaries.py
├── unit/
│   ├── auth/
│   ├── identity/
│   ├── catalog/
│   ├── booking/
│   ├── payment/
│   └── shared/
├── integration/
│   ├── api/
│   ├── repositories/
│   └── database/
├── e2e/
│   ├── test_guest_book_pay_flow.py
│   ├── test_user_account_bookings_flow.py
│   └── test_studio_dashboard_flow.py
├── factories/
│   ├── users.py
│   ├── studios.py
│   ├── services.py
│   ├── occurrences.py
│   └── bookings.py
└── conftest.py
```

## Classification Rules

- [ ] `architecture/`: import boundaries, module rules, file-size architecture guards.
- [ ] `unit/`: pure service/policy/helper logic with no HTTP and no real DB.
- [ ] `integration/api/`: real FastAPI app + test DB + HTTP client.
- [ ] `integration/repositories/`: repository queries against test DB.
- [ ] `integration/database/`: migrations, constraints, indexes, lifecycle jobs.
- [ ] `e2e/`: full critical product flows. Keep small and high-value.
- [ ] `factories/`: reusable builders, no hidden shared mutable state.

## Required Coverage Before Frontend Scale-Up

- [ ] OTP login / refresh / logout.
- [ ] `GET/PATCH /auth/me`.
- [ ] `GET /studios/my`.
- [ ] Studio CRUD + permissions.
- [ ] Service CRUD + visibility.
- [ ] `GET /studios/{studio_id}/services`.
- [ ] Schedule template generation behavior.
- [ ] Occurrence cancellation.
- [ ] Instructor assignment.
- [ ] Check-in / no-show.
- [ ] Booking create -> checkout -> webhook paid.
- [ ] `GET /bookings/my`.
- [ ] Owner bookings.
- [ ] Orders API.
- [ ] Refund flow if FR-04 is implemented.
- [ ] GDPR delete-account flow if FR-06 is implemented.

## Edge Case Tests

- [ ] Concurrent last-seat booking.
- [ ] Delayed Stripe webhook.
- [ ] Duplicate Stripe webhook.
- [ ] Payment failed -> pending booking/order expires.
- [ ] Soft-deleted user cannot authenticate.
- [ ] Guest booking/order attaches to verified user.
- [ ] Schedule edit rule does not mutate generated occurrences.
- [ ] Archived service with future bookings remains historically visible.

## Migration Steps

1. Inventory current tests and map each file to the target folder.
2. Move tests without changing assertions.
3. Run the full suite.
4. Extract duplicate fixtures into factories only after the move is green.
5. Add missing tests for new frontend-readiness work.

## Definition of Done

```bash
cd backend
uv run pytest -q
uv run lint-imports
uv run ruff check .
uv run pyright
```

- [ ] All tests live under `backend/tests/`.
- [ ] Test names make the scenario and expected result obvious.
- [ ] No integration test depends on another test's mutable state.
- [ ] Critical frontend flows can be tested before building UI around them.

## Out of Scope

- Playwright frontend tests. Keep those under the frontend app when added.
- Rewriting all tests for style only.
