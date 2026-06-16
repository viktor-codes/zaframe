# Domain Vocabulary Refactor — File-by-File Checklist

Companion to [domain-vocabulary.md](./domain-vocabulary.md).

**Legend:** `[ ]` todo · `[R]` rename file · `[S]` split/move content · `[D]` delete after move · `[M]` DB migration only

Execute phases in order. Do not start Phase 3 until Phase 2 migration applies cleanly.

---

## Phase 0 — Prep

- [x] Read ADR-002 end-to-end; agree on optional rename `ScheduleGenerateRequest` → `OccurrenceGenerateRequest`
- [x] Create branch `refactor/domain-vocabulary`
- [x] Baseline: `cd backend && uv run pytest` and frontend build green

---

## Phase 1 — Schemas reorganisation (no DB)

### 1.1 Create / split schema modules

| Action | File | Tasks |
|--------|------|-------|
| [x] | `backend/app/schemas/occurrence.py` | **Create** from `slot.py` |
| [x] | `backend/app/schemas/slot.py` | **Deleted** |
| [x] | `backend/app/schemas/catalog.py` | **Create** |
| [x] | `backend/app/schemas/order.py` | **Create** |
| [x] | `backend/app/schemas/service.py` | **Slimmed** |
| [x] | `backend/app/schemas/schedule.py` | **Merged** ScheduleTemplate* |
| [x] | `backend/app/schemas/booking.py` | Renamed base/list/occurrence fields |
| [x] | `backend/app/schemas/__init__.py` | Updated exports |
| [x] | `backend/app/schemas/search.py` | Unchanged |

### 1.3 Phase 1 gate

- [x] `uv run ruff check backend/app/schemas`
- [x] `uv run pytest` — 141 passed
- [x] No imports from deleted `schemas/slot.py`

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

---

## Phase 2 — Models, migration, repositories, services ✅

### 2.1 Alembic

| Action | File | Tasks |
|--------|------|-------|
| [x] | `backend/alembic/versions/005_domain_vocabulary.py` | Rename tables, columns, indexes, FKs; `single_class` → `single`; downgrade |
| [x] | `backend/alembic/versions/001_initial_schema.py` | **Do not edit** (applied) |
| [x] | `backend/alembic/versions/002_booking_active_uniqueness.py` | **Do not edit** |
| [x] | `backend/alembic/versions/003_booking_active_idx.py` | Revision id shortened (varchar 32 limit) |

**005 covers:**

- [x] `slots` → `occurrences`
- [x] `schedules` → `schedule_templates`
- [x] `bookings.slot_id` → `occurrence_id`
- [x] `occurrences.schedule_id` → `schedule_template_id`
- [x] Index `idx_slots_studio_service_start_time` → `idx_occurrences_studio_service_start_time`
- [x] Indexes `uq_bookings_slot_*` → `uq_bookings_occurrence_*`
- [x] `services.type` value migration `single_class` → `single`

### 2.2–2.5 Models, repos, core, services

All items completed (`Occurrence`, `ScheduleTemplate`, `OccurrenceRepository`, `uow.occurrences`, etc.).

### 2.6 Phase 2 gate

- [x] `uv run alembic upgrade head`
- [x] `uv run pytest` — 141 passed

---

## Phase 3 — API layer ✅

### 3.1 Routers & mappers

| Action | File | Tasks |
|--------|------|-------|
| [x] | `backend/app/api/v1/occurrences.py` | `/occurrences`; param `occurrence_id` |
| [x] | `backend/app/api/v1/studios.py` | `/occurrences`, `/generate-occurrences` |
| [x] | `backend/app/api/v1/bookings.py` | `BookingSelfListItem`, `occurrence_id` |
| [x] | `backend/app/api/v1/services.py` | `ScheduleTemplate*`; `/schedule-templates` CRUD |
| [x] | `backend/app/api/mappers/service.py` | `PublicOccurrence`, catalog imports |
| [x] | `backend/app/main.py` | `occurrences.router` |

### 3.2 Phase 3 gate

- [x] OpenAPI `/docs` reflects new paths
- [x] `uv run pytest` — 141 passed

---

## Phase 4 — Tests & scripts ✅

### 4.1 Backend tests

All listed test files updated; renamed:

- `test_api_studios_occurrences_bookings.py`
- `integration/test_generate_occurrences.py`

### 4.2 Seeds & docs

- [x] `seed_and_simulate.py`, `seed_100_studios.py`
- [x] `backend/docs/adr/001-datetime-and-studio-timezone.md`
- [x] `backend/tests/TEST_COVERAGE_REPORT.md`
- [x] `backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md` — retired (see docs/ARCHITECTURE.md historical note)

---

## Phase 5 — Frontend (big-bang) ✅

### 5.1–5.3 Types, API client, pages

All items completed (`occurrence.ts`, `occurrences.ts`, `occurrence_id`, `BookingSelfListItem`, etc.).

### 5.4 Service type enum

- [x] No `single_class` in `frontend/src`

### 5.5 Phase 5 gate

- [x] `npm run build`
- [ ] Manual smoke: studio public page → book → pay → my bookings (manual)

---

## Phase 6 — Final verification ✅

- [x] `uv run pytest` — 141 passed
- [x] Grep clean in `backend/app` and `frontend/src` (old symbols only in ADR, applied migrations 001–003, migration 005 downgrade)
- [x] `.env.example` — no slot-specific vars; unchanged
- [ ] `uv run ruff check .` — pre-existing import-order warnings in tests (unrelated to vocabulary)
- [ ] Suggested commit: `refactor(api): domain vocabulary Occurrence, ScheduleTemplate, schema split`

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
