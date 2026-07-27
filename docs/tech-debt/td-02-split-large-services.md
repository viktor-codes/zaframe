# TD-02 — Split oversized service modules (P1) — PARTIAL

> **Status (Jul 2026):** Original Part A/C mostly landed. `booking` already has
> `lifecycle` / `queries` / `mapping` / `persistence` / `repository/`.
>
> **Wave 3 leftover (A→E plan):**
> - `payment/checkout.py` (~460) — split session/order/helpers
> - `booking/service.py` (~256) — extract attendance → `attendance.py`
> - `booking/router.py` (~317) — split customer vs studio/attendance HTTP
> - `payment/repository.py` (~252) — deferred (out of Wave 3 A→E)

> Read [README.md](./README.md). Do **td-01** first if touching `catalog/service/service.py`.

## Problem

Project rule: functions/components **≤ 150 lines**; several modules violate this.

### Original hotspots (historical)

| File | ~Lines then | Concerns mixed |
|------|-------------|----------------|
| `payment/service.py` | 438 | checkout creation, access checks, capacity simulation, webhook confirm |
| `booking/service.py` | 370 | CRUD, authz mapping, lifecycle, persist helpers |
| `catalog/service/service.py` | 317 | CRUD + availability (smaller after td-01) |
| `booking/repository.py` | 300 | many query variants |

### Current hotspots (Jul 2026 re-measure)

| File | ~Lines | Next action |
|------|--------|-------------|
| `payment/checkout.py` | ~460 | Split (Wave 3 B) |
| `booking/router.py` | ~317 | Split routers (Wave 3 D) |
| `booking/service.py` | ~256 | Extract attendance (Wave 3 C) |
| `payment/repository.py` | ~252 | Deferred |
| `catalog/service/service.py` | ~133 | Done (CRUD) |
| `payment/service.py` | ~20 | Done (shim) |

## Goal

Split by **single responsibility** without changing HTTP routes or business behaviour.
Each new file **≤ 150 lines** where practical.

---

## Part A — `payment` module

### Target layout

```
modules/payment/
├── service.py          # thin re-export facade OR delete after router imports submodules
├── checkout.py         # create_checkout_session, create_order_checkout_session
├── confirmation.py     # confirm_booking_after_payment, confirm_order_after_payment
├── capacity.py         # _would_exceed_*, _apply_in_memory_*, _handle_overbooked_payment
├── access.py           # is_own_order, _assert_*_checkout_access
└── stripe_client.py    # _get_stripe_client, _checkout_session_expires_at (optional)
```

### Steps

1. `git mv` is not needed — extract functions with cut/paste into new modules.
2. Move symbols per table above; keep module-level constants (`PAYMENT_STATUS_*`) in
   `confirmation.py` or `__init__.py`.
3. `payment/service.py` becomes a **compatibility shim** re-exporting public functions:
   ```python
   from app.modules.payment.checkout import create_checkout_session, create_order_checkout_session
   from app.modules.payment.confirmation import confirm_booking_after_payment, confirm_order_after_payment
   ```
   OR update `router.py` + `webhooks.py` to import from submodules and **delete** `service.py`.
4. `payment/__init__.py` — export only what other domains need (likely nothing beyond
   `ProcessedWebhookEventRepository`; payment service fns stay internal).

### Tests

All existing `test_payment_service.py`, `test_webhooks.py`, integration payment tests must
pass without modification (if shim used) or with import path updates only.

---

## Part B — `booking` module

### Target layout

```
modules/booking/
├── service.py           # create_booking, cancel, queries, attach_guest — OR split further
├── lifecycle.py         # expire_stale_pending, complete_past_confirmed
├── queries.py           # get_bookings, get_my_bookings, get_owner_*, counts
├── mapping.py           # map_booking_for_user, map_booking_created_response
├── persistence.py       # see td-05 — may land here or in parallel
└── repository/          # OPTIONAL: split repo if still > 150 lines
    ├── queries.py
    └── commands.py
```

### Steps

1. Extract `lifecycle.py` first (smallest, no router impact).
2. Extract `mapping.py` (pure functions, easy tests).
3. Extract `queries.py` (read paths).
4. Leave `create_booking`, `cancel_booking`, persist helpers in `service.py` until td-05.
5. Update `booking/__init__.py` lazy `__getattr__` `_SERVICE_FUNCTIONS` tuple to include
   lifecycle exports if they remain public (`expire_stale_pending`, `complete_past_confirmed`
   used by `scripts/run_booking_lifecycle.py`).

### Repository split (if still > 150 lines after service split)

Split `booking/repository.py` into:
- `repository/read.py` — list/get/count methods
- `repository/write.py` — add, attach, flush helpers

Single `BookingRepository` class can inherit both mixins or compose — keep one class exported
from `booking/__init__.py`.

---

## Part C — `catalog/service` (after td-01)

If `service.py` still > 150 lines:

```
catalog/service/
├── service.py      # CRUD only: create/get/update/deactivate
└── availability.py  # check_course_availability*, get_service_availability
```

Update `catalog/service/__init__.py` lazy exports accordingly.

---

## Constraints

- No API route/path changes.
- No new dependencies between domains.
- Routers continue importing from published interfaces (`app.modules.payment...`).

## Definition of Done

```bash
wc -l app/modules/payment/*.py app/modules/booking/*.py app/modules/catalog/service/*.py
# No file > 200 lines (150 target; 200 hard gate for this step)
uv run pytest -q  # 172+ passed
uv run lint-imports  # KEPT
```

## Commit

One commit per part OR single commit if done atomically:

```
refactor(payment): split service into checkout, confirmation, capacity
refactor(booking): split service into lifecycle, queries, mapping
refactor(catalog): split service CRUD from availability
```

## Out of scope

Changing payment overbook refund behaviour; repository query optimisation.
