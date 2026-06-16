# TZ-06 — Move `occurrence` into `modules/catalog/occurrence`

> Read [README.md](./README.md). Depends on tz-05. Router stays in `api/v1/` until tz-10.

## Goal & why
`occurrence` = concrete bookable time instances. Move its CRUD service, repository, schemas.
The `occurrence_generator` (schedule-driven creation) is **not** here — it lands in
`catalog/schedule` in tz-07.

## Files (`git mv`)
| From | To |
|------|----|
| `app/services/occurrence.py` | `app/modules/catalog/occurrence/service.py` |
| `app/repositories/occurrence_repo.py` | `app/modules/catalog/occurrence/repository.py` |
| `app/schemas/occurrence.py` | `app/modules/catalog/occurrence/schemas.py` |
| _(new)_ | `app/modules/catalog/occurrence/__init__.py` |

## Steps
1. `git mv` files; create `__init__.py`.
2. In-file imports: keep `app.core.*`, `app.models.occurrence`, `app.schemas.occurrence` →
   change self-import to `from app.modules.catalog.occurrence.schemas import ...`.
   `service.py` also calls `uow.bookings.count_confirmed_by_occurrence` (no import needed).
3. Published interface — `app/modules/catalog/occurrence/__init__.py`:
   ```python
   from app.modules.catalog.occurrence.repository import OccurrenceRepository
   from app.modules.catalog.occurrence.schemas import (
       OccurrenceCreate, OccurrenceResponse, OccurrenceUpdate, OccurrenceWithBookings,
   )
   from app.modules.catalog.occurrence.service import (
       create_occurrence, delete_occurrence, get_occurrence, get_occurrence_or_raise,
       get_occurrences, get_occurrences_count, update_occurrence,
   )
   __all__ = [...]
   ```
   Extend `app/modules/catalog/__init__.py` to re-export `OccurrenceRepository`.
4. Schema facade — `app/schemas/__init__.py`: re-export occurrence schemas from the new
   submodule. **Keep** any `model_rebuild()` ordering for `OccurrenceWithBookings` /
   `BookingWithOccurrence` (cross-refs with booking schemas resolve later).
5. Repo wiring — `core/uow.py` + `app/repositories/__init__.py`: import
   `OccurrenceRepository` from `app.modules.catalog.occurrence`. `uow.occurrences` unchanged.
6. Repoint callers `from app.services.occurrence import ...` → `from app.modules.catalog.occurrence import ...`:
   - `app/api/v1/occurrences.py`, `app/api/v1/studios.py`.
   - `app/services/service.py` uses `uow.occurrences` (repo), not the occurrence service —
     grep to confirm no service-level import.

## Grep targets
```bash
rg -n "app\.services\.occurrence|app\.repositories\.occurrence_repo|app\.schemas\.occurrence" backend
```
Allowed: none.

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(catalog): move occurrence into modules/catalog/occurrence
```

## Out of scope
`occurrence_generator` (tz-07); occurrences router relocation (tz-10); ORM model.
