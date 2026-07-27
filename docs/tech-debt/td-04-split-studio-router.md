# TD-04 — Decompose `catalog/studio/router.py` god-router (P2) — PARTIAL

> **Status (Jul 2026):** Cross-domain handlers already moved:
> - `catalog/public/router.py` — `GET /studios/slug/{slug}/public`
> - `catalog/schedule/router.py` — `POST /studios/{id}/generate-occurrences`
> - `catalog/occurrence` — `studio_occurrence_router` for `GET /studios/{id}/occurrences`
>
> **Still oversized:** `studio/router.py` (~224), `occurrence/router.py` (~241),
> `service/router.py` (~236). Wave 3 E: trim each to ≤150 without URL changes.

> Read [README.md](./README.md).

## Problem

`modules/catalog/studio/router.py` originally owned HTTP for **five concerns**:

| Route | Real owner | Status |
|-------|------------|--------|
| `GET/POST/PATCH/DELETE /studios` | studio ✓ | stays |
| `GET /studios/{id}/occurrences` | occurrence (nested) | moved |
| `GET /studios/slug/{slug}/public` | public | moved |
| `POST /studios/{id}/generate-occurrences` | schedule | moved |
| `GET /studios` with `include_services` | studio + search shape | still in studio |
| `GET /studios/{id}/services` | service (nested) | Wave 3 E candidate |

Routers should stay thin; cross-subdomain routes obscure ownership.

## Goal

**Same URLs, same response models** — only relocate handlers to owning routers.
`api/router.py` registration order must preserve path matching (FastAPI first-match).

## Target state

### 1. Move to `catalog/occurrence/router.py`

```python
occurrence_router = APIRouter(prefix="/occurrences", tags=["occurrences"])
studio_occurrence_router = APIRouter(prefix="/studios", tags=["studios"])

@studio_occurrence_router.get("/{studio_id}/occurrences", ...)
async def list_studio_occurrences(...): ...
```

Export `studio_occurrence_router` from `catalog/occurrence/__init__.py` or router module.

### 2. Move to `catalog/public/router.py` (NEW small file)

```python
public_router = APIRouter(prefix="/studios", tags=["studios"])

@public_router.get("/slug/{slug}/public", response_model=StudioPublicResponse)
async def get_studio_public_endpoint(...): ...
```

`public/` previously had no router — add one.

### 3. Move to `catalog/schedule/router.py` (NEW)

```python
schedule_router = APIRouter(prefix="/studios", tags=["studios"])

@schedule_router.post("/{studio_id}/generate-occurrences", ...)
async def generate_studio_occurrences_endpoint(...): ...
```

### 4. Keep in `catalog/studio/router.py`

- CRUD `/studios`, `/studios/count`, `/studios/{studio_id}`
- `include_services` explore list (or extract to `studio/explore.py` helper if router still > 150 lines)

### 5. Update `api/router.py`

Include additional routers **before or after** studio router as needed:

```python
api_v1.include_router(studio_router)
api_v1.include_router(studio_occurrence_router)  # from occurrence
api_v1.include_router(public_router)             # from catalog.public
api_v1.include_router(schedule_router)           # from catalog.schedule
```

**Critical:** verify no path conflicts. `/studios/slug/{slug}/public` must not be captured
by `/studios/{studio_id}` — today `slug` is a literal segment so order matters:
register `public_router` **before** `studio_router` if `{studio_id}` could capture `slug`
(currently `GET /studios/{studio_id}` vs `GET /studios/slug/...` — safe if slug route kept).

Run OpenAPI diff mentally: same paths under `/api/v1`.

## Tests

- `tests/test_api_studios_occurrences_bookings.py` — must pass unchanged.
- Manual/automated: `GET /api/v1/studios/slug/{slug}/public`, `POST .../generate-occurrences`.

## Constraints

- Routers import only **published interfaces** (`from app.modules.catalog.studio import ...`).
- No business logic in routers — keep delegating to services.
- Each router file **≤ 150 lines**.

## Definition of Done

- `studio/router.py` ≤ 150 lines.
- `wc -l modules/catalog/*/router.py` — all ≤ 150.
- `uv run pytest -q` 172+ passed.
- `/docs` shows identical paths.

## Commit

```
refactor(catalog): split studio god-router across occurrence, public, schedule
```

## Out of scope

Renaming URL paths; versioning API to v2.
