# TZ-10 — Relocate routers, add `api/router.py` aggregator, drop facades

> Read [README.md](./README.md). Depends on tz-01…tz-09. Medium-high risk (broad but
> mechanical). This step makes the modular layout *final* and removes temporary scaffolding.

## Goal & why
Move the remaining cross-cutting routers into their modules, introduce a single router
aggregator, slim `main.py`, relocate `model_rebuild()`, and delete the legacy facade
packages (`app/services`, `app/repositories`, `app/schemas`). After this step there is no
`app.services.*` / `app.schemas.*` / `app.repositories.*` left.

## Part A — Move routers into modules
| From | To | Repoint imports to |
|------|----|--------------------|
| `app/api/v1/studios.py` | `app/modules/catalog/studio/router.py` | `app.modules.catalog.studio` / `.occurrence` / `.schedule` / `.public` published interfaces |
| `app/api/v1/services.py` | `app/modules/catalog/service/router.py` | `app.modules.catalog.service` / `.schedule` / `.studio` |
| `app/api/v1/occurrences.py` | `app/modules/catalog/occurrence/router.py` | `app.modules.catalog.occurrence` / `.studio`, `app.modules.booking` |
| `app/api/v1/bookings.py` | `app/modules/booking/router.py` | `app.modules.booking`, `app.modules.booking.order` |
| `app/api/v1/health.py` | `app/api/health.py` | unchanged (infra) |

Each moved router: replace every `from app.schemas import ...` with imports from the owning
module's published interface (e.g. `from app.modules.catalog.occurrence import OccurrenceResponse`).

## Part B — Mappers
Split `app/api/mappers/service.py` by response owner:
- `map_course_availability`, `map_course_booking_result` → `app/modules/booking/order/mappers.py`.
- `map_studio_public`, `_map_public_service` → `app/modules/catalog/public/mappers.py`.
- `map_service_availability` → `app/modules/catalog/service/mappers.py`.
Update router imports accordingly; delete `app/api/mappers/` when empty.

## Part C — Shared repository base
`git mv app/repositories/base.py app/core/repository.py`; update every
`from app.repositories.base import WriteRepositoryMixin` → `from app.core.repository import WriteRepositoryMixin`
across all module repositories.

## Part D — Router aggregator + slim main
1. Create `app/api/router.py`:
   ```python
   from fastapi import APIRouter
   from app.api.health import router as health_router
   from app.modules.auth.router import router as auth_router
   from app.modules.booking.router import router as booking_router
   from app.modules.catalog.occurrence.router import router as occurrence_router
   from app.modules.catalog.service.router import router as service_router
   from app.modules.catalog.studio.router import router as studio_router
   from app.modules.payment.router import router as payment_router
   from app.modules.payment.webhooks import router as webhooks_router
   from app.modules.search.router import router as search_router

   api_v1 = APIRouter(prefix="/api/v1")
   for r in (studio_router, service_router, occurrence_router, booking_router,
             payment_router, auth_router, search_router):
       api_v1.include_router(r)

   def register_routers(app) -> None:
       app.include_router(health_router)               # root /health
       app.include_router(health_router, prefix="/api/v1")
       app.include_router(api_v1)
       app.include_router(webhooks_router)             # root /webhooks
   ```
2. `app/main.py`: remove all per-router imports/includes; call `register_routers(app)`.
   Keep middleware, exception handlers, lifespan.

## Part E — Relocate `model_rebuild()`
Move the `*.model_rebuild()` block from `app/schemas/__init__.py` into `app/api/router.py`
(module import time, after all router imports pull in every schema). Import the schema
classes from their module published interfaces.

## Part F — Delete facades
Once nothing references them (grep), delete:
- `app/schemas/` (entire package)
- `app/services/` (entire package, incl. `dto/`)
- `app/repositories/` (entire package; `base.py` already moved in Part C)
Update `alembic/env.py` and `tests/` if they import `app.models` (models stay) — they should
be unaffected.

## Grep targets (MUST be zero)
```bash
rg -n "app\.services|app\.schemas|app\.repositories|app\.api\.v1|app\.api\.mappers" backend/app backend/scripts
```
(`app.models` and `app.core` remain valid.)

## Definition of Done
- `uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.
- `app/schemas`, `app/services`, `app/repositories`, `app/api/v1`, `app/api/mappers` no
  longer exist.
- OpenAPI `/docs` shows the exact same routes/paths as before (no API change).

## Commit
```
refactor(api): add module router aggregator, slim main, drop facades
```

## Out of scope
New import-linter independence contracts and boundary tests (tz-11).
