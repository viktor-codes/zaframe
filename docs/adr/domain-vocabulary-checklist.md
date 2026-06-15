# Domain Vocabulary Refactor — File-by-File Checklist

Companion to [domain-vocabulary.md](./domain-vocabulary.md).

**Legend:** `[ ]` todo · `[R]` rename file · `[S]` split/move content · `[D]` delete after move · `[M]` DB migration only

Execute phases in order. Do not start Phase 3 until Phase 2 migration applies cleanly.

---

## Phase 0 — Prep

- [ ] Read ADR-002 end-to-end; agree on optional rename `ScheduleGenerateRequest` → `OccurrenceGenerateRequest`
- [ ] Create branch `refactor/domain-vocabulary`
- [ ] Baseline: `cd backend && uv run pytest` and frontend build green

---

## Phase 1 — Schemas reorganisation (no DB)

### 1.1 Create / split schema modules

| Action | File | Tasks |
|--------|------|-------|
| [S] | `backend/app/schemas/occurrence.py` | **Create** from `slot.py`: `OccurrenceBase`, `OccurrenceCreate`, `OccurrenceUpdate`, `OccurrenceResponse`, `OccurrenceWithBookings`, `OccurrenceStatusLiteral` |
| [D] | `backend/app/schemas/slot.py` | Remove after occurrence.py lands |
| [S] | `backend/app/schemas/catalog.py` | **Create**: move `PublicService`, `PublicOccurrence` (was `PublicServiceOccurrence`), `StudioPublicResponse` from `service.py` |
| [S] | `backend/app/schemas/order.py` | **Create**: move `OrderBase`, `OrderResponse`, `CourseBookingPreviewItem`, `CourseAvailabilityResult`, `CourseBookingCreate`, `CourseBookingResponse` |
| [S] | `backend/app/schemas/service.py` | **Slim**: keep only `ServiceBase/Create/Update/Response`, `ServiceAvailabilityScheduleItem`, `ServiceAvailabilityResponse` |
| [S] | `backend/app/schemas/schedule.py` | **Merge**: add `ScheduleTemplateBase/Create/Response` (was `Schedule*` in service.py); keep `ScheduleGenerateRequest` (or rename to `OccurrenceGenerateRequest`) |
| [ ] | `backend/app/schemas/booking.py` | `BookingClientBase` → `BookingResponseBase`; `BookingListItem` → `BookingSelfListItem`; `slot_id` → `occurrence_id` in fields; import `OccurrenceResponse` |
| [ ] | `backend/app/schemas/__init__.py` | Update exports, `model_rebuild()` targets |
| [ ] | `backend/app/schemas/search.py` | Update imports if `ServiceResponse` / `StudioResponse` paths change (likely unchanged) |

### 1.2 Schema rename reference (grep targets)

```
SlotBase              → OccurrenceBase
SlotCreate            → OccurrenceCreate
SlotUpdate            → OccurrenceUpdate
SlotResponse          → OccurrenceResponse
SlotWithBookings      → OccurrenceWithBookings
SlotStatusLiteral     → OccurrenceStatusLiteral
ScheduleBase          → ScheduleTemplateBase
ScheduleCreate        → ScheduleTemplateCreate
ScheduleResponse      → ScheduleTemplateResponse
PublicServiceOccurrence → PublicOccurrence
BookingClientBase     → BookingResponseBase
BookingListItem       → BookingSelfListItem
slot_id (schema fields) → occurrence_id
```

### 1.3 Phase 1 gate

- [ ] `uv run ruff check backend/app/schemas`
- [ ] `uv run pyright backend/app/schemas` (if configured project-wide, run full backend)
- [ ] No imports from deleted `schemas/slot.py`

---

## Phase 2 — Models, migration, repositories, services

### 2.1 Alembic

| Action | File | Tasks |
|--------|------|-------|
| [M] | `backend/alembic/versions/004_domain_vocabulary.py` | **Create**: rename tables, columns, indexes, FKs; `single_class` → `single`; document downgrade |
| [ ] | `backend/alembic/versions/001_initial_schema.py` | **Do not edit** (applied) — reference only when writing 004 |
| [ ] | `backend/alembic/versions/002_booking_active_uniqueness.py` | **Do not edit** — recreate index names in 004 |
| [ ] | `backend/alembic/versions/003_booking_expired_completed_indexes.py` | **Do not edit** |

**004 must cover:**

- [ ] `slots` → `occurrences`
- [ ] `schedules` → `schedule_templates`
- [ ] `bookings.slot_id` → `occurrence_id`
- [ ] `occurrences.schedule_id` → `schedule_template_id`
- [ ] Index `idx_slots_studio_service_start_time` → `idx_occurrences_studio_service_start_time`
- [ ] Indexes `uq_bookings_slot_*` → `uq_bookings_occurrence_*`
- [ ] `services.type` value migration `single_class` → `single`

### 2.2 Models

| Action | File | Tasks |
|--------|------|-------|
| [R] | `backend/app/models/occurrence.py` | Rename from `slot.py`; class `Occurrence`, `OccurrenceStatus`; FK `schedule_template_id` |
| [R] | `backend/app/models/schedule_template.py` | Rename from `schedule.py`; class `ScheduleTemplate` |
| [ ] | `backend/app/models/booking.py` | `occurrence_id`; relationship `occurrence`; update unique index `__table_args__` |
| [ ] | `backend/app/models/service.py` | `ServiceType.SINGLE = "single"`; remove `SINGLE_CLASS` |
| [ ] | `backend/app/models/studio.py` | Relationship `occurrences` (was `slots`) |
| [ ] | `backend/app/models/__init__.py` | Export `Occurrence`, `OccurrenceStatus`, `ScheduleTemplate`; remove `Slot`, `Schedule` |

### 2.3 Repositories

| Action | File | Tasks |
|--------|------|-------|
| [R] | `backend/app/repositories/occurrence_repo.py` | Rename from `slot_repo.py`; `OccurrenceRepository` |
| [R] | `backend/app/repositories/schedule_template_repo.py` | Rename from `schedule_repo.py`; `ScheduleTemplateRepository` |
| [ ] | `backend/app/repositories/booking_repo.py` | All `slot_id` / `Slot` references → `occurrence_id` / `Occurrence` |
| [ ] | `backend/app/repositories/studio_repo.py` | Occurrence queries if any |
| [ ] | `backend/app/repositories/service_repo.py` | Schedule template joins if any |
| [ ] | `backend/app/repositories/__init__.py` | Export new repo class names |

### 2.4 Core

| Action | File | Tasks |
|--------|------|-------|
| [ ] | `backend/app/core/uow.py` | `occurrences: OccurrenceRepository`, `schedule_templates: ScheduleTemplateRepository` |
| [ ] | `backend/app/core/booking_holds.py` | Terminology / field names if referenced |
| [ ] | `backend/app/core/datetime_utils.py` | Comments mentioning Slot/Schedule |

### 2.5 Services

| Action | File | Tasks |
|--------|------|-------|
| [R] | `backend/app/services/occurrence.py` | Rename from `slot.py` |
| [ ] | `backend/app/services/booking.py` | `uow.occurrences`, `occurrence_id`, schema types |
| [ ] | `backend/app/services/service.py` | ScheduleTemplate*, generate occurrences, `ServiceType.SINGLE` |
| [ ] | `backend/app/services/studio.py` | Occurrence listing / generate endpoint logic |
| [ ] | `backend/app/services/payment.py` | `occurrence` / `occurrence_id` references |
| [ ] | `backend/app/services/search.py` | If slot/service joins exist |
| [ ] | `backend/app/services/dto/service.py` | `occurrence_id` in DTOs; consider split `dto/catalog.py`, `dto/order.py` (optional) |
| [ ] | `backend/app/services/dto/__init__.py` | Updated exports |

### 2.6 Phase 2 gate

- [ ] `uv run alembic upgrade head` on clean DB
- [ ] `uv run pytest backend/tests` — expect failures until Phase 3 API wired; fix repo/service/unit tests here

---

## Phase 3 — API layer

### 3.1 Routers & mappers

| Action | File | Tasks |
|--------|------|-------|
| [R] | `backend/app/api/v1/occurrences.py` | Rename from `slots.py`; prefix `/occurrences`; param `occurrence_id` |
| [ ] | `backend/app/api/v1/studios.py` | `/occurrences`, `/generate-occurrences`; response models |
| [ ] | `backend/app/api/v1/bookings.py` | `BookingSelfListItem`, `occurrence_id` in creates |
| [ ] | `backend/app/api/v1/services.py` | `ScheduleTemplate*` schemas; schedule CRUD paths review (`/schedules/` → `/schedule-templates/` optional — **decide**) |
| [ ] | `backend/app/api/mappers/service.py` | `PublicOccurrence`, catalog imports |
| [ ] | `backend/app/main.py` | `from app.api.v1 import occurrences`; `include_router(occurrences.router)` |

**Open decision (mark in PR description):**

- [ ] `DELETE /services/schedules/{id}` → `DELETE /services/schedule-templates/{id}` ?

### 3.2 Phase 3 gate

- [ ] OpenAPI `/docs` reflects new paths
- [ ] `uv run pytest backend/tests`

---

## Phase 4 — Tests & scripts

### 4.1 Backend tests

| File | Tasks |
|------|-------|
| [ ] `backend/tests/test_api_studios_slots_bookings.py` | Rename file → `test_api_studios_occurrences_bookings.py`; update paths |
| [ ] `backend/tests/integration/test_generate_schedule.py` | → `test_generate_occurrences.py` |
| [ ] `backend/tests/test_booking_lifecycle.py` | `occurrence_id` |
| [ ] `backend/tests/test_booking_schema_serialization.py` | `BookingSelfListItem`, `BookingResponseBase` |
| [ ] `backend/tests/test_booking_holds.py` | Terminology |
| [ ] `backend/tests/test_attach_guest_bookings.py` | |
| [ ] `backend/tests/test_payment_service.py` | |
| [ ] `backend/tests/test_stripe_checkout.py` | |
| [ ] `backend/tests/test_webhooks.py` | |
| [ ] `backend/tests/integration/test_payments.py` | |
| [ ] `backend/tests/integration/test_booking_duplicate.py` | |
| [ ] `backend/tests/integration/test_bookings_authz.py` | |
| [ ] `backend/tests/integration/test_overbooking_confirm.py` | |

### 4.2 Seeds & docs

| File | Tasks |
|------|-------|
| [ ] `backend/scripts/seed_and_simulate.py` | `ServiceType.SINGLE`, `Occurrence` |
| [ ] `backend/scripts/seed_100_studios.py` | Same |
| [ ] `backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md` | Terminology pass |
| [ ] `backend/docs/adr/001-datetime-and-studio-timezone.md` | Replace “slot” with “occurrence” where policy text |
| [ ] `backend/tests/TEST_COVERAGE_REPORT.md` | Optional update |

---

## Phase 5 — Frontend (big-bang)

### 5.1 Types

| Action | File | Tasks |
|--------|------|-------|
| [R] | `frontend/src/types/occurrence.ts` | Rename from `slot.ts`; `OccurrenceResponse`, etc. |
| [ ] | `frontend/src/types/booking.ts` | `occurrence_id`, `BookingSelfListItem`, nested `OccurrenceResponse` |
| [ ] | `frontend/src/types/studio.ts` | Public catalog types if duplicated |
| [ ] | `frontend/src/types/index.ts` | Re-exports |

### 5.2 API client

| Action | File | Tasks |
|--------|------|-------|
| [R] | `frontend/src/lib/api/occurrences.ts` | Rename from `slots.ts`; `/api/v1/occurrences` |
| [ ] | `frontend/src/lib/api/studios.ts` | `fetchStudioOccurrences`, `generateOccurrences` |
| [ ] | `frontend/src/lib/api/bookings.ts` | `BookingSelfListItem`, `occurrence_id` |
| [ ] | `frontend/src/lib/api/index.ts` | Export occurrences module |

### 5.3 Pages & components

| File | Tasks |
|------|-------|
| [ ] `frontend/src/app/(main)/studios/[id]/page.tsx` | Occurrence types, API calls |
| [ ] `frontend/src/app/(main)/studios/[id]/book/page.tsx` | `occurrence_id` |
| [ ] `frontend/src/app/(main)/bookings/page.tsx` | `BookingSelfListItem` |
| [ ] `frontend/src/app/(main)/bookings/[id]/confirm/page.tsx` | |
| [ ] `frontend/src/app/(main)/dashboard/studios/[id]/page.tsx` | Generate occurrences UI |
| [ ] `frontend/src/app/(main)/dashboard/page.tsx` | If slot references exist |
| [ ] `frontend/src/components/ui/Badge.tsx` | Only if slot-specific copy |

### 5.4 Service type enum on frontend

- [ ] Grep `single_class` → `single` across `frontend/src`

### 5.5 Phase 5 gate

- [ ] `npm run build` (or `pnpm`) in `frontend/`
- [ ] Manual smoke: studio public page → book → pay → my bookings

---

## Phase 6 — Final verification

- [ ] Full backend: `uv run ruff check . && uv run pytest`
- [ ] Grep zero hits (except ADR/history): `slot_id`, `SlotRepository`, `single_class`, `BookingClientBase`, `BookingListItem`, `PublicServiceOccurrence`, `/slots`
- [ ] `.env.example` — no slot-specific vars expected; confirm unchanged
- [ ] Commit message: `refactor(api): domain vocabulary Occurrence, ScheduleTemplate, schema split`

---

## Quick grep commands (run from repo root)

```bash
# Should trend to zero during refactor
rg -n 'slot_id|SlotRepository|single_class|BookingClientBase|BookingListItem|PublicServiceOccurrence|/slots' \
  --glob '!docs/adr/*' --glob '!alembic/versions/00[123]*'

# New symbols should appear
rg -n 'Occurrence|occurrence_id|ScheduleTemplate|BookingSelfListItem|PublicOccurrence' backend frontend
```

---

## Suggested PR slicing (optional)

If the work feels too large for one PR:

1. **PR1** — Phase 1 schemas only (temporary imports from old model names OK)
2. **PR2** — Phase 2 models + migration + repos + services + tests
3. **PR3** — Phase 3–5 API + frontend

For solo dev, a **single PR** is also fine if CI stays green.
