# TZ-05 — Move `studio` into `modules/catalog/studio`

> Read [README.md](./README.md). Router stays in `api/v1/` until tz-10 (README §1.9).

## Goal & why
First slice of `catalog`. `studio` service is small and self-contained (CRUD + ownership
check). Move service + repo + schemas; repoint callers.

## Preconditions
- Branch `refactor/modular-monolith`, tests green.

## Files (`git mv`)
| From | To |
|------|----|
| `app/services/studio.py` | `app/modules/catalog/studio/service.py` |
| `app/repositories/studio_repo.py` | `app/modules/catalog/studio/repository.py` |
| `app/schemas/studio.py` | `app/modules/catalog/studio/schemas.py` |
| _(new)_ | `app/modules/catalog/__init__.py`, `app/modules/catalog/studio/__init__.py` |

## Steps
1. Create `app/modules/catalog/__init__.py` (empty) + studio package.
2. `git mv` the three files.
3. In-file imports: keep `app.core.*`, `app.models.studio`. `schemas.py` keep as-is.
4. Published interface — `app/modules/catalog/studio/__init__.py`:
   ```python
   from app.modules.catalog.studio.repository import StudioRepository
   from app.modules.catalog.studio.schemas import (
       StudioCreate, StudioResponse, StudioUpdate, StudioWithOccurrences,
   )
   from app.modules.catalog.studio.service import (
       create_studio, delete_studio, ensure_studio_owner,
       get_studio, get_studio_or_raise, get_studios, get_studios_count, update_studio,
   )
   __all__ = [...]  # all names above
   ```
   Also re-export from `app/modules/catalog/__init__.py` for the package-level published
   interface (so other modules can do `from app.modules.catalog import StudioRepository`):
   ```python
   from app.modules.catalog.studio import StudioRepository  # extend in later steps
   ```
5. Schema facade — `app/schemas/__init__.py`: re-export Studio schemas from
   `app.modules.catalog.studio.schemas`. (`StudioBase` may not be re-exported in the module
   `__init__`; import it directly from the schemas submodule in the facade.)
6. Repo wiring — `core/uow.py` + `app/repositories/__init__.py`: import `StudioRepository`
   from `app.modules.catalog.studio` (or `app.modules.catalog`). `uow.studios` unchanged.
7. **Repoint callers** of `from app.services.studio import ...` → `from app.modules.catalog.studio import ...`:
   - `app/api/v1/studios.py`, `app/api/v1/services.py`, `app/api/v1/occurrences.py`.
   - `app/services/service.py` does **not** import studio service (it uses `uow.studios`), but grep to confirm.

## Grep targets
```bash
rg -n "app\.services\.studio|app\.repositories\.studio_repo|app\.schemas\.studio" backend
```
Allowed: none.

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(catalog): move studio into modules/catalog/studio
```

## Out of scope
studios router relocation (tz-10); Studio ORM model.
