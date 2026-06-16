# TD-06 — Relocate `get_bookings_count` from occurrence module (P2)

> Read [README.md](./README.md).

## Problem

`catalog/occurrence/service.py` exposes:

```python
async def get_bookings_count(uow: UnitOfWork, occurrence_id: int) -> int:
    return await uow.bookings.count_confirmed_by_occurrence(occurrence_id)
```

Occurrence domain service delegates to booking repository — blurred responsibility.
Likely legacy from pre-modular layout.

## Goal

Remove the function from occurrence service. Callers use `booking` published API or inline
the one-liner in the router if truly HTTP-only.

## Steps

1. Grep usages:
   ```bash
   rg "get_bookings_count" backend
   ```
2. For each caller:
   - If router-only: replace with `from app.modules.booking import ...` count helper OR
     add `count_confirmed_by_occurrence` to booking published interface:
     ```python
     # booking/service.py
     async def count_confirmed_bookings_for_occurrence(uow, occurrence_id: int) -> int:
         return await uow.bookings.count_confirmed_by_occurrence(occurrence_id)
     ```
     Export via `booking/__init__.py` lazy exports.
   - If unused: delete `get_bookings_count` from occurrence service with no replacement.
3. Remove from `catalog/occurrence/__init__.py` if exported.
4. Update any tests referencing `app.modules.catalog.occurrence.get_bookings_count`.

## Constraints

- `catalog` must not import `booking` module (import-linter). **Routers** may import both —
  move orchestration to `occurrence/router.py` if the count is needed for a response field.

## Definition of Done

- `occurrence/service.py` has no `uow.bookings` references.
- `uv run lint-imports` KEPT.
- `uv run pytest -q` 172+ passed.

## Commit

```
refactor(occurrence): remove booking count from occurrence service
```

## Out of scope

New API fields; N+1 optimisation on occurrence list endpoints.
