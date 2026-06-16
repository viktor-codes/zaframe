# Modular Monolith Refactor — Agent Task Pack

Master spec for the `app/services|repositories|schemas` → `app/modules/<domain>` migration.
Decision and rationale: [ADR-003](../adr/003-modular-monolith.md).

**Audience:** coding agents. Each `tz-NN-*.md` is one self-contained step. Read THIS file
first — it holds the rules every step must obey. Do **only** what your `tz-NN` says.

---

## 0. Golden rules (apply to every step)

1. **Behaviour-preserving.** No API route, request/response shape, DB schema, or business
   logic changes — **except** the two explicitly-scoped exceptions (god-module split in
   `tz-07`, `is_own_booking` promotion in `tz-09`). This is a *move + import rewrite*.
2. **Preserve history:** move files with `git mv`, never delete-and-recreate.
3. **Models stay put.** Do **not** move anything in `app/models/`. The relational graph is a
   shared persistence layer by design (ADR-003 §2).
4. **Published interface.** Every module exposes its public surface via
   `app/modules/<domain>/__init__.py` (repository class + any public service functions /
   policies other modules legitimately use). Other modules import from
   `app.modules.<domain>`, **never** from internal paths like
   `app.modules.<domain>.service`.
5. **No private cross-domain imports.** Importing a `_underscore` name from another domain
   is forbidden. If another module needs it, it must be promoted to the public interface
   (only where a step says so) — otherwise leave it internal.
6. **UoW stays flat & data-only.** Keep plural repo attributes (`uow.bookings`,
   `uow.occurrences`). Never add logic methods to the UoW. `core/uow.py` imports repository
   classes from each module's published interface.
7. **Temporary facades are allowed.** To keep the suite green mid-migration, the legacy
   aggregators `app/schemas/__init__.py`, `app/services/__init__.py`,
   `app/repositories/__init__.py` may re-export from the new module locations. They are
   collapsed/removed in `tz-10`. `model_rebuild()` stays in `app/schemas/__init__.py` until
   `tz-10` relocates it.
8. **DTOs follow their domain.** `app/services/dto/*` move into the module that produces
   them (specified per step).
9. **Router timing.** Leaf-domain routers (search, payment, auth) move with their domain
   (tz-01/-02/-04). The **cross-cutting catalog & booking routers stay in `app/api/v1/`**
   through tz-05…tz-09 — only their import lines are repointed to module published
   interfaces. They are relocated into their modules in **tz-10** together with the
   `api/router.py` aggregator. Reason: `studios.py` alone pulls studio + occurrence +
   schedule + public, so moving it early would thrash.

---

## 1. Target layout (reference)

```
app/
├── models/                 # UNCHANGED — central ORM + Base
├── core/                   # uow, database, config, security, exceptions, datetime_utils, middleware
├── integrations/           # stripe/, email/  (external adapters)
├── modules/
│   ├── search/      {__init__, router, service, repository, schemas}.py
│   ├── payment/     {__init__, router, webhooks, service, repository, schemas}.py
│   ├── identity/    {__init__, router, service, repository, schemas}.py
│   ├── auth/        {__init__, router, service, repository, schemas}.py
│   ├── catalog/
│   │   ├── studio/      {__init__, router, service, repository, schemas}.py
│   │   ├── service/     {__init__, router, service, repository, schemas, dto}.py
│   │   ├── occurrence/  {__init__, router, service, repository, schemas}.py
│   │   ├── schedule/    {__init__, service, repository, schemas}.py   # occurrence_generator
│   │   └── public/      {__init__, router, service}.py               # get_studio_public
│   └── booking/
│       ├── {__init__, router, service, repository, schemas, policies}.py
│       └── order/   {__init__, service, repository, schemas, dto}.py # create_course_booking
└── api/
    ├── deps.py
    └── router.py           # aggregates every modules/*/router.py
```

> `email.py` → `app/integrations/email/service.py`. `integrations/stripe/` already exists.

---

## 2. Definition of Done (every step)

Run from `backend/`:

```bash
uv run ruff check .          # 0 new errors
uv run lint-imports          # all contracts KEPT
uv run pytest -q             # 170 passed (never fewer)
```

Plus:
- `rg "app\.(services|repositories|schemas)\.<moved_symbol>"` returns **only** allowed
  temporary-facade hits (or zero). Each step lists its grep targets.
- The module's `__init__.py` exports its public surface.
- Test patch paths updated (e.g. `unittest.mock.patch("app.services.auth.send_otp_email")`
  must point at the new location).

If a gate is red, fix within the step's scope; do not expand scope.

---

## 3. Execution order & dependencies

| Step | Domain | Depends on | Risk |
|------|--------|-----------|------|
| tz-01 | search | — | low |
| tz-02 | payment (+ webhooks) | — | low |
| tz-03 | identity (User) | — | low |
| tz-04 | auth (otp, refresh, login, jwt) + email→integrations | tz-03 | medium |
| tz-05 | catalog/studio | — | low |
| tz-06 | catalog/occurrence | tz-05 | low |
| tz-07 | catalog/service + schedule (god-module split) | tz-05, tz-06 | **high** |
| tz-08 | catalog/public | tz-07 | medium |
| tz-09 | booking + order (move course booking, promote is_own_booking) | tz-02, tz-07 | **high** |
| tz-10 | api/router.py aggregator, slim main.py, relocate model_rebuild, drop facades | all | medium |
| tz-11 | architecture guards (import-linter independence, test_boundaries, ARCHITECTURE.md) | tz-10 | low |

tz-01..tz-06 are largely independent and may be done in any order / parallel branches.
tz-07 and tz-09 are the substantive ones — assign your strongest agent.

---

## 4. Commit messages (Conventional Commits)

One commit per step:

```
refactor(search):    move search into modules/search
refactor(payment):   move payment + stripe webhooks into modules/payment
refactor(identity):  extract identity (User) into modules/identity
refactor(auth):      move auth into modules/auth; email into integrations
refactor(catalog):   move studio into modules/catalog/studio
refactor(catalog):   move occurrence into modules/catalog/occurrence
refactor(catalog):   split service god-module into service/schedule
refactor(catalog):   move public studio view into modules/catalog/public
refactor(booking):   move booking + order into modules/booking, add policies
refactor(api):       add module router aggregator, slim main, drop facades
test(api):           enforce module boundaries via import-linter + test_boundaries
```

---

## 5. Cross-domain coupling map (today → target)

| Caller | Imports (today) | Target |
|--------|-----------------|--------|
| `services/payment.py` | `booking.is_own_booking` | `from app.modules.booking import is_own_booking` (promoted to `booking/policies.py` in tz-09) |
| `services/service.py` | `booking._ensure_no_active_booking_for_guest`, `booking._persist_bookings` | gone — `create_course_booking` moves INTO `booking/order` (tz-09) and calls them in-domain |
| `services/auth.py` | `booking.attach_guest_bookings`, `user.get_or_create_user`, `user.get_user_by_id`, `email.send_otp_email` | published interfaces: `app.modules.booking`, `app.modules.identity`, `app.integrations.email` |
| `api/mappers/service.py` | `app.schemas`, `app.services.dto` | split between `catalog` and `booking/order` mappers/schemas (tz-07/-08/-09) |

Until tz-09 lands, `payment` and `service` may keep their current imports pointing at the
**new** booking location once booking moves; before that, leave them at the legacy path via
the temporary facade. Never deepen coupling.
