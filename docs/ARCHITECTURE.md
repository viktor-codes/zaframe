# ZeeFrame Backend — Modular Monolith Architecture

Decision record: [ADR-003](./adr/003-modular-monolith.md).

## Historical note

Pre-modular-monolith improvement notes lived in `backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md`
(superseded by ADR-003, 2026-06).

## Package layout

```
backend/app/
├── api/                    # HTTP aggregation (router.py, health) — top layer
├── core/                   # Infrastructure: config, security, UoW, deps, database
├── integrations/           # External adapters (stripe, email)
├── models/                 # Shared SQLAlchemy ORM (central persistence graph)
└── modules/
    ├── auth/
    ├── identity/
    ├── payment/
    ├── search/
    ├── booking/ (+ order/)
    └── catalog/
        ├── studio/
        ├── service/
        ├── occurrence/
        ├── schedule/
        └── public/
```

Each domain module exposes its **published interface** via `app/modules/<domain>/__init__.py`.
Other modules import from that package root — never from internal paths like `.service` or `.repository`.

## Layer rule (within a module)

```
router → service → repository → core / models
```

- **Routers** — HTTP only: parsing, status codes, `Depends`.
- **Services** — business logic; receive `UnitOfWork`, never open sessions directly.
- **Repositories** — SQLAlchemy queries only; must not import `service`, `router`, or `policies`.
- **Models** — ORM mapping; no imports from `app.modules` or `app.api`.

Shared request dependencies (`get_uow`, `get_current_user`) live in `app.core.deps`.
`UnitOfWork` type is in `app.core.uow`; repository wiring is in `app.core.uow_factory`.

## Allowed cross-domain edges

| Caller | May import (public API only) |
|--------|------------------------------|
| `booking` | `catalog`, `identity`, `core`, `models`, `integrations` |
| `payment` | `booking`, `identity`, `core`, `models`, `integrations` |
| `auth` | `booking`, `identity`, `core`, `models`, `integrations` |
| `catalog` | `identity`, `core`, `models` (not `booking`, `payment`, `auth`) |
| `identity` | `core`, `models` only (leaf) |
| `search` | `core`, `models` only (read-only leaf) |
| Any module | `integrations`, `core`, `models` |
| `core.uow_factory` | all repository classes (UoW wiring — see ADR-003 §3) |

Private names (`_foo`) are domain-internal and must not be imported across domains.

## Module dependency graph

```mermaid
flowchart TB
    subgraph top ["HTTP"]
        API["app.api"]
    end

    subgraph modules ["app.modules"]
        AUTH[auth]
        ID[identity]
        PAY[payment]
        BOOK[booking]
        CAT[catalog]
        SRCH[search]
    end

    subgraph infra ["Infrastructure"]
        CORE[core]
        MODELS[models]
        INT[integrations]
    end

    API --> AUTH & PAY & BOOK & CAT & SRCH
    AUTH --> BOOK & ID
    PAY --> BOOK & ID
    BOOK --> CAT & ID
    CAT --> ID
    SRCH --> CORE
    ID --> CORE
    AUTH & PAY & BOOK & CAT --> CORE
    CORE --> MODELS
    AUTH --> INT
    PAY --> INT
```

## Boundary enforcement

| Tool | Command | What it checks |
|------|---------|----------------|
| import-linter | `uv run lint-imports` | Forbidden import directions (see `pyproject.toml`) |
| AST tests | `pytest tests/architecture/` | Repositories don't import upper layers; no `_` cross-domain imports |
| Ruff | `uv run ruff check .` | Style and import order |
| Pyright | `uv run pyright app scripts` | Strict static typing for application code |

`import-linter` ignores transitive imports through `core.deps` → `core.uow_factory` for leaf
modules — the monolithic UoW intentionally wires every repository in one factory (ADR-003 §3).

## Running checks locally

From `backend/`:

```bash
uv run ruff check .
uv run lint-imports
uv run pyright app scripts
uv run pytest -q
```

Or from the repo root: `make lint` / `make test`.

## Background jobs

Scheduled maintenance runs outside the FastAPI process. Scripts live in `backend/scripts/`
and use `uow_scope()` — same transaction boundary as the app.

| Job | Script | Schedule (prod) | Purpose |
|-----|--------|-----------------|---------|
| Booking lifecycle | `scripts/run_booking_lifecycle.py` | Every 5 min (UTC) | Expire stale `pending` holds/orders; mark past `confirmed` bookings as `completed` |
| OTP cleanup | `scripts/pg_cron_otp_cleanup.sql` | Daily (pg_cron on DB) | Delete OTP rows older than retention window |

### Booking lifecycle (Render cron — Option A)

Production uses a **Render Cron Job** defined in root `render.yaml`:

- Service: `zaframe-booking-lifecycle`
- Schedule: `*/5 * * * *` (UTC)
- Command: `python -m scripts.run_booking_lifecycle` (from `backend/` rootDir)

The script is **idempotent**: safe to re-run; each invocation logs
`booking_lifecycle_complete` with `expired_count` and `completed_count`.
When all bookings in a pending order expire, the order becomes `expired` and its checkout
access token is cleared.
If Stripe later reports a successful payment that cannot safely confirm seats, the order/payment
ledger moves to `manual_review` instead of being shown as a normal paid booking.

**Manual / local ops:**

```bash
make booking-lifecycle
# or: cd backend && uv run python -m scripts.run_booking_lifecycle
```

**Monitoring (log-based, no external tooling required):**

- Spike in `expired_count` per run → investigate checkout/payment funnel abandonment.
- Missing `booking_lifecycle_complete` for 3+ consecutive intervals (~15 min) → cron failure;
  check Render dashboard (Trigger Run for debug) and `DATABASE_URL` on the cron service.

Alternatives not used: always-on worker loop (Option B), HTTP internal endpoint (Option D).
See [TD-11](./tech-debt/td-11-booking-lifecycle-cron.md).
