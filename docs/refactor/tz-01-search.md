# TZ-01 — Move `search` into `modules/search` (reference step)

> Read [README.md](./README.md) first. This step is the **template** for tz-02…tz-06.
> Goal: prove the move pattern on the lowest-risk, least-coupled domain.

## Goal & why
`search` has the smallest surface (1 service fn, 1 repo, 1 schema, 1 router) and no inbound
domain dependencies. Moving it first validates the published-interface + UoW-wiring pattern
with minimal blast radius.

## Preconditions
- On branch `refactor/modular-monolith`, baseline `uv run pytest` green (170).

## Files (use `git mv`)
| From | To |
|------|----|
| `app/repositories/search_repo.py` | `app/modules/search/repository.py` |
| `app/services/search.py` | `app/modules/search/service.py` |
| `app/schemas/search.py` | `app/modules/search/schemas.py` |
| `app/api/v1/search.py` | `app/modules/search/router.py` |
| _(new)_ | `app/modules/__init__.py` (empty) |
| _(new)_ | `app/modules/search/__init__.py` |

## Steps
1. Create `app/modules/__init__.py` (empty) and the `search` package dir.
2. `git mv` the four files as per the table.
3. **Fix in-file imports** in the moved files:
   - `repository.py`: keep `from app.models...`, `from app.repositories.base import WriteRepositoryMixin` (base stays in `app/repositories/base.py` for now).
   - `service.py`: `from app.schemas import SearchResult, ServiceResponse, StudioResponse` may stay (facade) — it works because `app/schemas/__init__.py` still re-exports. Leave as-is.
   - `router.py`: update `from app.services.search import ...` → `from app.modules.search.service import ...`. Keep `from app.api.deps import ...`.
4. **Published interface** — `app/modules/search/__init__.py`:
   ```python
   from app.modules.search.repository import SearchRepository
   from app.modules.search.schemas import SearchQueryParams, SearchResult

   __all__ = ["SearchRepository", "SearchQueryParams", "SearchResult"]
   ```
5. **Schema facade** — `app/schemas/__init__.py`: change the search import line to re-export
   from the new location so `from app.schemas import SearchResult, SearchQueryParams` keeps
   working everywhere:
   ```python
   from app.modules.search.schemas import SearchQueryParams, SearchResult
   ```
   (delete the old `from app.schemas.search import ...` line; keep names in `__all__`).
6. **Repository wiring**:
   - `app/repositories/__init__.py`: replace `from app.repositories.search_repo import SearchRepository` with `from app.modules.search import SearchRepository` (facade keeps old import path alive).
   - `core/uow.py`: change the `SearchRepository` import to `from app.modules.search import SearchRepository`. Leave the other repos as the bulk `from app.repositories import (...)` for now (they migrate in their own steps). `uow.search` attribute name is unchanged.
7. **Router wiring** — `app/main.py`: update `from app.api.v1 import ... search ...`. Since
   `search` left `api/v1`, import it from the new path:
   ```python
   from app.modules.search.router import router as search_router
   ...
   app.include_router(search_router, prefix="/api/v1")
   ```
   Remove `search` from the `from app.api.v1 import (...)` line.

## Grep targets (must be clean except facades)
```bash
rg -n "app\.services\.search|app\.repositories\.search_repo|app\.schemas\.search|app\.api\.v1\.search" backend
```
Allowed remaining hits: none (facade re-exports use `app.modules.search`).

## import-linter
No new contract required this step (independence contracts land in tz-11). Existing
contracts must stay KEPT.

## Definition of Done
- `uv run ruff check . && uv run lint-imports && uv run pytest -q` → green, 170 passed.
- `app/modules/search/` contains the 4 files + `__init__.py`.

## Commit
```
refactor(search): move search into modules/search
```

## Out of scope
Do not touch `repositories/base.py`, other domains, or `model_rebuild()`.
