# TZ-08 — Move the public storefront view into `modules/catalog/public`

> Read [README.md](./README.md). Depends on tz-07. Router stays in `api/v1/` until tz-10.

## Goal & why
`catalog/public` is the anonymous storefront aggregate: it reads studios + services +
occurrences and shapes them for the public studio page. Currently `get_studio_public` is a
**temporary tenant** in `catalog/service/service.py` (from tz-07). Move it to its own
sub-domain with its DTOs and public schemas.

## Files
| From | To |
|------|----|
| `get_studio_public` (in `catalog/service/service.py`) | `app/modules/catalog/public/service.py` |
| `PublicServiceDTO`, `PublicServiceAvailabilityDTO`, `StudioPublicDTO` (in `catalog/service/dto.py`) | `app/modules/catalog/public/dto.py` |
| `app/schemas/catalog.py` | `app/modules/catalog/public/schemas.py` (`PublicOccurrence`, `PublicService`, `StudioPublicResponse`) |
| _(new)_ | `app/modules/catalog/public/__init__.py` |

## Steps
1. Create `catalog/public/` package.
2. Move `get_studio_public` out of `catalog/service/service.py` into
   `catalog/public/service.py`. Remove its temporary re-export from
   `catalog/service/__init__.py`.
3. Move the three public DTOs from `catalog/service/dto.py` to `catalog/public/dto.py`.
   `catalog/service/dto.py` keeps the availability + course DTOs.
4. `git mv app/schemas/catalog.py app/modules/catalog/public/schemas.py`.
5. In-file imports:
   - `public/service.py`: `from app.modules.catalog.public.dto import PublicServiceDTO, PublicServiceAvailabilityDTO, StudioPublicDTO`; `from app.modules.catalog.service import <availability helpers it still needs>` (e.g. `get_capacity_status` is on the `Service` model, so likely none); keep `app.core.*`, `app.models`. It uses `service.get_capacity_status(...)` from the ORM model — no service import needed.
   - `public/schemas.py`: keep as-is.
6. Published interface — `catalog/public/__init__.py`:
   ```python
   from app.modules.catalog.public.dto import StudioPublicDTO
   from app.modules.catalog.public.schemas import (
       PublicOccurrence, PublicService, StudioPublicResponse,
   )
   from app.modules.catalog.public.service import get_studio_public
   __all__ = [...]
   ```
7. Facades:
   - `app/schemas/__init__.py`: re-export `PublicOccurrence`, `PublicService`,
     `StudioPublicResponse` from `app.modules.catalog.public.schemas`.
   - `app/services/dto/__init__.py`: repoint the three public DTOs to
     `app.modules.catalog.public.dto` (others still from `catalog/service.dto`).
8. Repoint callers:
   - `app/api/v1/studios.py`: `get_studio_public` → `from app.modules.catalog.public import get_studio_public`.
   - `app/api/mappers/service.py`: `StudioPublicDTO`, `PublicServiceDTO` imports → public DTO path; `StudioPublicResponse`, `PublicService` stay via `app.schemas` facade.

## Grep targets
```bash
rg -n "app\.schemas\.catalog|get_studio_public" backend
```
`get_studio_public` should resolve only via `app.modules.catalog.public`.

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(catalog): move public studio view into modules/catalog/public
```

## Out of scope
Course-booking move (tz-09); router relocation (tz-10).
