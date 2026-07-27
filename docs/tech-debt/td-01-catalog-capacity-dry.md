# TD-01 — Extract shared overbooking logic into `catalog/capacity.py` (P1)

> **Status: Done.** Shared helpers live in `catalog/capacity.py` (+ `capacity_types.py`);
> catalog service/public callers use them; unit tests green.

> Read [README.md](./README.md). **Highest-impact DRY fix** from the post-refactor review.

## Problem

Overbooking / capacity math is duplicated in:

| File | What it duplicates |
|------|-------------------|
| `modules/catalog/service/service.py` | `_evaluate_course_availability`, `get_service_availability` per-occurrence loop |
| `modules/catalog/public/service.py` | `get_studio_public` course card availability block (lines ~70–107) |

Both call `service.get_capacity_status(...)`, compute soft/hard flags, `overbooked_ratio`
vs `service.max_overbooked_ratio`, and derive `can_book` / `requires_warning`.

Changing overbooking rules today requires editing two places — regression risk.

## Goal

Single **pure-function** module inside catalog that both services call. No new cross-domain
imports. `catalog` must still not import `app.modules.booking` (import-linter).

## Target file

```
app/modules/catalog/capacity.py   # NEW — pure functions + small dataclasses
```

Optionally export key symbols from `app/modules/catalog/__init__.py` if other catalog
submodules need them (not required for external domains).

## Design

### 1. Types (dataclasses, frozen)

```python
@dataclass(frozen=True, slots=True)
class OccurrenceFill:
    occurrence_id: int
    max_capacity: int
    confirmed_count: int
    pending_count: int

    @property
    def current_total(self) -> int: ...

@dataclass(frozen=True, slots=True)
class OccurrenceCapacityFlags:
    is_over_soft: bool
    is_over_hard: bool
    remaining: int
    total_after_one_booking: int

@dataclass(frozen=True, slots=True)
class CourseCapacitySummary:
    can_book: bool
    requires_warning: bool
    hard_block: bool
    overbooked_count: int
    total_occurrences: int
```

### 2. Pure functions (no `uow`, no DB)

```python
def classify_occurrence_capacity(
    service: Service,
    *,
    max_capacity: int,
    current_bookings: int,
    requested: int = 1,
) -> OccurrenceCapacityFlags:
    """Wrap Service.get_capacity_status + derived fields."""

def is_occurrence_overbooked(flags: OccurrenceCapacityFlags) -> bool:
    return flags.is_over_soft or flags.is_over_hard

def evaluate_course_capacity_summary(
    service: Service,
    fills: list[OccurrenceFill],
    *,
    requested_per_occurrence: int = 1,
) -> CourseCapacitySummary:
    """
    Shared ratio logic:
    - hard_block if any HARD_LIMIT or overbooked_ratio > max_overbooked_ratio
    - requires_warning if any soft/hard but not hard_block
    - can_book if not hard_block and at least one seat somewhere (caller may refine)
    """

def build_public_course_availability(
    service: Service,
    fills: list[OccurrenceFill],
    *,
    occurrence_dates: list[date],  # parallel to fills, for overbooked_dates
) -> PublicServiceAvailabilityDTO:
    """Maps summary → PublicServiceAvailabilityDTO for storefront cards."""
```

### 3. Refactor callers

**`catalog/service/service.py`:**
- `_evaluate_course_availability` → build `list[OccurrenceFill]` from `_CapacityStats`,
  call `evaluate_course_capacity_summary`, map to `CourseAvailabilityDTO` (keep DTO shape).
- `get_service_availability` per-occurrence loop → `classify_occurrence_capacity` per stat.

**`catalog/public/service.py`:**
- Replace inline loop (lines ~75–107) with:
  1. Build `OccurrenceFill` list from `occurrence_capacity_map`.
  2. `build_public_course_availability(...)`.

## Tests

Add `backend/tests/unit/test_catalog_capacity.py`:

| Test | Assert |
|------|--------|
| `test_classify_occurrence_capacity_under_soft_limit` | no soft/hard |
| `test_classify_occurrence_capacity_soft_limit` | `is_over_soft` |
| `test_evaluate_course_capacity_summary_hard_block_on_ratio` | ratio > `max_overbooked_ratio` |
| `test_evaluate_course_capacity_summary_warning_only` | soft occurrences, ratio OK |
| `test_build_public_course_availability_maps_dates` | `overbooked_dates` populated |

Reuse patterns from `tests/test_service_helpers.py` (Service capacity ratios).

Existing integration tests (`test_course_booking_occurrences`, API studios public) must
still pass unchanged.

## Constraints

- **No** `uow` in `capacity.py` — keeps it unit-testable and import-linter-safe.
- **No** moving `Service.get_capacity_status` off the ORM model yet (optional future step).
- File must stay **< 150 lines**; split types vs functions if needed.

## Definition of Done

- `rg "get_capacity_status" backend/app/modules/catalog` — only `capacity.py` + model (service files call capacity helpers, not raw status logic duplicated).
- `uv run pytest tests/unit/test_catalog_capacity.py -q` green.
- Full suite: 172+ passed.
- `uv run lint-imports` KEPT.

## Commit

```
refactor(catalog): extract shared capacity logic into catalog/capacity
```

## Out of scope

Caching public page; changing overbooking business rules.
