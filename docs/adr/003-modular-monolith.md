# ADR-003: Modular Monolith — Package by Domain, Shared Persistence

**Status:** Accepted
**Date:** 2026-06-16
**Related:** [ADR-002 — Domain Vocabulary](./domain-vocabulary.md) · [ADR-001 — Date/Time Policy](../../backend/docs/adr/001-datetime-and-studio-timezone.md)

## Context

The backend is organised **by technical layer** (`api/`, `services/`, `repositories/`,
`models/`, `schemas/`). Understanding a single domain (e.g. booking) requires opening
five folders. As the product and (future) team grow, two concrete problems hurt:

1. **Low cohesion.** A domain is scattered across layers; no single place tells the
   "booking" story.
2. **Hidden coupling that violates SOLID.** Domains import each other's *private*
   functions:
   - `services/service.py` imports `booking._ensure_no_active_booking_for_guest`,
     `booking._persist_bookings`.
   - `services/payment.py` imports `booking.is_own_booking`.
   - `services/auth.py` imports `booking.attach_guest_bookings`, `user.*`, `email.*`.
3. **God-module.** `services/service.py` (~718 lines) owns six responsibilities across
   three domains (service CRUD, schedule-template CRUD, occurrence generation, course
   availability, course-order creation, public studio view) — an SRP violation.

What already works and is **kept**: the `UnitOfWork` exposes *flat repositories*
(`uow.bookings`, `uow.occurrences`), and services are functions taking `uow`. That is
the "UoW = data glue, not logic glue" pattern we want.

## Decision

### 1. Package by domain (`app/modules/`)

```
app/modules/<domain>/{router,service,repository,schemas,policies}.py
```

Domains: `catalog` (sub-domains `studio`, `service`, `occurrence`, `schedule`, `public`),
`booking` (+ `order`), `auth`, `identity`, `payment`, `search`.

### 2. ORM models stay centralised in `app/models/` — deliberate, not a compromise

The relational graph (`Studio↔Service↔Occurrence↔Booking↔Order↔User`) is one dense,
FK-connected unit queried with cross-domain `joinedload`. The database is already a
**shared integration point**. Splitting models per module would buy little (models carry
no logic, per project rules) while introducing circular-import / mapper-registry risk.

Trade-off accepted: full per-module extraction (Phase 3 "vision") will require splitting
models later. **YAGNI** until then.

### 3. UnitOfWork stays flat and data-only

- Attributes remain repositories named in the plural: `uow.bookings`, `uow.occurrences`.
- **Forbidden:** `uow.booking.create_booking()` (logic on the UoW).
- `core/uow.py` imports each repository from its module's **published interface**
  (`from app.modules.booking import BookingRepository`), not from internal paths — so
  internal file moves do not ripple into the UoW.

### 4. Cross-domain rules (the real fix)

| Pattern | Resolution |
|---------|-----------|
| Course order living in `catalog/service.py` | **Move** `create_course_booking` into `modules/booking/order/`. It then calls booking helpers inside its own domain. |
| `payment` needs `is_own_booking` | Promote to `booking/policies.py` and export via booking's published interface. |
| `auth` orchestrates booking + identity + email | Legitimate orchestration — allowed, but **only via published interfaces**, never private (`_`) names. |

**Invariant:** a module may call another module's *public* API; private (`_`) names are
domain-internal. Logic lives in services, queries in repositories — enforced by tests.

### 5. Boundary guards (`import-linter`)

Contracts in `pyproject.toml` (`uv run lint-imports`) enforce dependency direction and
domain independence. Tightened phase-by-phase; wired into CI.

## Consequences

**Positive**

- One folder per domain → onboarding and navigation are immediate.
- Coupling is removed (moved into the owning domain) instead of hidden behind new paths.
- Architecture is machine-checked; drift fails CI, not review.
- Public API routes are unchanged, so `apps/web` is not affected by the move.

**Negative / risks**

- Large diff; mitigated by phased migration with a green `pytest` (170 tests) gate per
  phase and `git mv` to preserve history.
- Central `models/` weakens the "module owns its tables" story for a future service split.
- Orchestration in `auth` keeps a fan-out dependency — acceptable, bounded by the
  published-interface rule.

## Migration phases

0. Prep — branch, baseline, `import-linter`, this ADR.
1. Scaffold `modules/`; move leaf domains (`search`, `payment`, `auth`, `identity`).
2. `catalog` + split the `service.py` god-module.
3. `booking` + `order` (move `create_course_booking`; `policies.py` for payment↔booking).
4. `api/router.py` aggregator; slim `main.py`; relocate `model_rebuild()`.
5. Guards — tighten `import-linter` contracts, add `tests/architecture/test_boundaries.py`,
   update `ARCHITECTURE.md`.

Each phase ends green (`uv run pytest`, `uv run lint-imports`, `uv run ruff check`).
