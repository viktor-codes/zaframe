# TD-05 — `booking/persistence.py` for intra-domain write helpers (P2)

> Read [README.md](./README.md). Best done alongside or after **td-02 Part B**.

## Problem

`booking/order/service.py` imports **private** symbols from sibling `booking/service.py`:

```python
from app.modules.booking.service import (
    _ensure_no_active_booking_for_guest,
    _persist_bookings,
)
```

Intra-domain, but fragile: private names signal "don't touch" yet `order` depends on them.
`test_boundaries.py` only blocks **cross-domain** `_` imports.

## Goal

Explicit intra-domain module for booking write persistence — no leading underscores on the
**module boundary** (functions can stay module-private with clear ownership).

## Target

```
app/modules/booking/persistence.py
```

Move from `booking/service.py`:

| Symbol | New name (drop leading `_` at module level) |
|--------|---------------------------------------------|
| `_ensure_no_active_booking_for_guest` | `ensure_no_active_booking_for_guest` |
| `_persist_booking` | `persist_booking` |
| `_persist_bookings` | `persist_bookings` |
| `_is_active_booking_unique_violation` | `is_active_booking_unique_violation` (if only used here) |

Keep `DUPLICATE_BOOKING_MESSAGE` in `service.py` or move to `persistence.py` — single source.

## Steps

1. Create `persistence.py` with moved functions (same logic, same exceptions).
2. `booking/service.py` `create_booking` imports from `booking.persistence`.
3. `booking/order/service.py`:
   ```python
   from app.modules.booking.persistence import ensure_no_active_booking_for_guest, persist_bookings
   ```
4. **Do NOT** add persistence functions to `booking/__init__.py` `__all__` — not part of
   published cross-domain API.
5. Extend `tests/architecture/test_boundaries.py` OPTIONAL (recommended):

```python
def test_booking_order_does_not_import_booking_service_private_names():
    """order submodule uses persistence, not service._private."""
    # AST check: booking/order/**/*.py must not import from app.modules.booking.service
    # symbols starting with _
```

## import-linter

No contract changes — all imports stay inside `app.modules.booking`.

## Tests

Existing tests cover behaviour:
- `test_booking_duplicate.py`
- `integration/test_course_booking_occurrences.py`
- `test_api_studios_occurrences_bookings.py`

No new tests required unless extracting broke edge cases.

## Definition of Done

```bash
rg "_ensure_no_active_booking_for_guest|_persist_bookings" backend/app/modules/booking
# → zero matches (only non-underscore names in persistence.py)
uv run pytest -q  # 172+ passed
```

## Commit

```
refactor(booking): extract write persistence into booking/persistence
```

## Out of scope

Extracting repository write logic; event outbox.
