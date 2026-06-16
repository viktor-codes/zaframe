# TZ-07 — Split the `service.py` god-module into `catalog/service` + `catalog/schedule`

> Read [README.md](./README.md). Depends on tz-05, tz-06. **High risk** — strongest agent.
> Router stays in `api/v1/` until tz-10.

## Goal & why
`app/services/service.py` (~718 lines) violates SRP: it owns service CRUD, schedule-template
CRUD, occurrence generation, course availability, course-order creation, and the public
studio view (ADR-003 §1.3). This step splits it by responsibility. Two functions are
**temporary tenants** that leave in later steps — handle them per the notes below.

## Target placement

| Symbol(s) in `services/service.py` | Destination |
|------------------------------------|-------------|
| `create_service`, `get_service`, `get_service_or_raise`, `update_service`, `deactivate_service` | `catalog/service/service.py` |
| `check_course_availability`, `check_course_availability_for_update`, `get_service_availability`, `_CapacityStats`, `_get_course_occurrences_with_capacity*`, `_build_course_capacity_stats`, `_evaluate_course_availability`, `_calculate_course_order_total_cents`, `_distribute_course_unit_prices` | `catalog/service/service.py` |
| `create_schedule_template`, `get_schedule_templates_for_service`, `get_schedule_template`, `get_schedule_template_or_raise`, `delete_schedule_template`, `occurrence_generator`, `_iterate_weeks` | `catalog/schedule/service.py` |
| `get_studio_public` | **temporary tenant** in `catalog/service/service.py` → moves to `catalog/public` in **tz-08** |
| `create_course_booking` | **temporary tenant** in `catalog/service/service.py` → moves to `booking/order` in **tz-09** |

## Files (`git mv` for repos/schemas; new files for the split service)
| From | To |
|------|----|
| `app/repositories/service_repo.py` | `app/modules/catalog/service/repository.py` |
| `app/repositories/schedule_template_repo.py` | `app/modules/catalog/schedule/repository.py` |
| `app/schemas/service.py` | `app/modules/catalog/service/schemas.py` |
| `app/schemas/schedule.py` | `app/modules/catalog/schedule/schemas.py` |
| `app/services/dto/service.py` | `app/modules/catalog/service/dto.py` |
| `app/services/service.py` | **split** into `catalog/service/service.py` + `catalog/schedule/service.py`, then `git rm` the original |

## Steps
1. Create packages `catalog/service/` and `catalog/schedule/` with `__init__.py`.
2. `git mv` the repos, schemas, and `dto/service.py` to the locations above.
3. Split `services/service.py` by the table. Use `git mv` to seed `catalog/service/service.py`
   from the original (preserves blame), then move schedule-related defs into
   `catalog/schedule/service.py`. Delete the emptied original if anything remains.
4. In-file imports after split:
   - `catalog/service/service.py`: `from app.modules.catalog.service.schemas import ServiceUpdate` (and others), `from app.modules.catalog.service.dto import ...`. For the temporary `create_course_booking` tenant, keep `from app.services.booking import _ensure_no_active_booking_for_guest, _persist_bookings` (facade; resolved in tz-09). Keep `app.core.*`, `app.models`.
   - `catalog/schedule/service.py`: `from app.modules.catalog.schedule.schemas import ScheduleTemplateCreate`, `app.core.*`, `app.models`.
   - repos: keep `app.models`, `app.repositories.base`.
   - `dto.py`: keep `from app.models import Booking, Order` (uses `from __future__ import annotations`).
5. Published interfaces:
   - `catalog/service/__init__.py` exports: `ServiceRepository`, service CRUD fns, availability fns (`check_course_availability`, `check_course_availability_for_update`, `get_service_availability`), the availability DTOs, **and temporarily** `create_course_booking`, `get_studio_public` (re-export so callers resolve; the re-export line is deleted when each tenant relocates).
   - `catalog/schedule/__init__.py` exports: `ScheduleTemplateRepository`, schedule CRUD fns, `occurrence_generator`.
   - extend `app/modules/catalog/__init__.py` to re-export `ServiceRepository`, `ScheduleTemplateRepository`.
6. Schema facades — `app/schemas/__init__.py`: re-export Service/Schedule schemas from the new
   submodules. **Keep** `model_rebuild()` calls.
7. DTO facade — `app/services/dto/__init__.py`: re-export every DTO from
   `app.modules.catalog.service.dto` (so `from app.services.dto import ...` keeps working in
   `api/mappers/service.py` and the bookings router until tz-09).
8. Repo wiring — `core/uow.py` + `app/repositories/__init__.py`: import `ServiceRepository`
   from `app.modules.catalog.service`, `ScheduleTemplateRepository` from
   `app.modules.catalog.schedule`. `uow.services`, `uow.schedule_templates` unchanged.
9. Repoint callers of `from app.services.service import ...`:
   - `app/api/v1/services.py`: CRUD + availability → `from app.modules.catalog.service import ...`; schedule-template fns → `from app.modules.catalog.schedule import ...`.
   - `app/api/v1/studios.py`: `get_studio_public` → `from app.modules.catalog.service import get_studio_public` (temp); `occurrence_generator` → `from app.modules.catalog.schedule import occurrence_generator`.
   - `app/api/v1/bookings.py`: `create_course_booking` → `from app.modules.catalog.service import create_course_booking` (temp).

## Guardrail
Keep each new `service.py` **under 150 lines** where practical (project rule). If
`catalog/service/service.py` stays large because of the two temporary tenants, that is
acceptable until tz-08/tz-09 remove them — note it in the PR description.

## Grep targets
```bash
rg -n "app\.services\.service|app\.repositories\.(service_repo|schedule_template_repo)|app\.schemas\.(service|schedule)|app\.services\.dto\.service" backend
```
Allowed: only the temporary booking-helper import inside `create_course_booking`.

## Definition of Done
`uv run ruff check . && uv run lint-imports && uv run pytest -q` → 170 passed.

## Commit
```
refactor(catalog): split service god-module into service/schedule
```

## Out of scope
Moving `get_studio_public` (tz-08) and `create_course_booking` (tz-09) to their final homes;
router relocation (tz-10).
