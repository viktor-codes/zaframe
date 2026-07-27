# Tech Debt Task Pack — Post Modular-Monolith Review

Companion to the architecture review after [ADR-003](../adr/003-modular-monolith.md) landed.
Each `td-NN-*.md` is one self-contained step for a coding agent.

**Baseline (must stay green after every step):**
```bash
cd backend && uv run ruff check . && uv run lint-imports && uv run pytest -q
```
Also in CI / `make lint`: `uv run pyright app scripts`.

---

## Golden rules

1. **Behaviour-preserving** unless the step explicitly says otherwise (only td-03 changes
   import paths, not semantics).
2. **Respect module boundaries** — `uv run lint-imports` must stay green; do not weaken
   contracts to make a step pass.
3. **150-line soft limit** per file (project rule) — splitting steps exist because several
   files violate this.
4. **One commit per step** — message at the bottom of each TZ.
5. **Tests required** when logic moves (td-01, td-03) or routes change (td-04); optional
   for pure docs (td-07).

---

## Priority map

| Priority | Step | Topic | Effort |
|----------|------|-------|--------|
| ✅ Done | [td-01](./td-01-catalog-capacity-dry.md) | DRY overbooking logic → `catalog/capacity.py` | done |
| 🟡 P2 | [td-02](./td-02-split-large-services.md) | Split oversized services — leftover: checkout done; booking attendance/router done | partial |
| ✅ Done | [td-03](./td-03-identity-ownership-policies.md) | Unify `is_own_booking` / `is_own_order` | done |
| ✅ Done | [td-04](./td-04-split-studio-router.md) | Studio god-router split across list/CRUD/public/schedule/occurrence/services | done |
| 🟡 P2 | [td-05](./td-05-booking-persistence-internal.md) | `booking/persistence.py` for intra-domain helpers | ~1.5h |
| 🟡 P2 | [td-06](./td-06-occurrence-bookings-count.md) | Relocate `get_bookings_count` from occurrence | ~1h |
| 🟢 P3 | [td-07](./td-07-docs-cleanup.md) | README vocabulary + retire stale plan doc | ~1h |
| 🟢 P3 | [td-08](./td-08-merge-prep.md) | PR checklist + optional history fix | ~30m |
| ✅ Done | [td-09](./td-09-pyright-ci.md) | Pyright strict in `make lint` + Backend CI | done |
| ✅ Done | [td-10](./td-10-e2e-book-pay-flow.md) | Playwright guest book → Checkout (Option A) | done |
| ✅ Done | [td-11](./td-11-booking-lifecycle-cron.md) | Production cron for booking lifecycle | done |

### Done notes

- **td-01:** Shared pure helpers in `catalog/capacity.py` (+ `capacity_types.py`);
  callers in `catalog/service` and `catalog/public`. Unit tests in
  `tests/unit/catalog/test_catalog_capacity.py`.
- **td-02 (partial):** payment checkout + booking attendance/router splits landed in
  Wave 3; `payment/repository.py` still oversized (deferred).
- **td-03:** `identity.policies.is_owned_by_user`; booking/payment thin wrappers;
  import-linter allows `payment → identity`. Unit tests in
  `tests/unit/identity/test_identity_policies.py`.
- **td-04:** Catalog HTTP split — `studio/list_router`, nested services,
  occurrence list/CRUD/`studio_occurrence_router`, service schedule-templates.
- **td-09:** `uv run pyright app scripts` in `Makefile` lint and `.github/workflows/backend-ci.yml`.
- **td-10:** Option A in `frontend/e2e/flows/guest-checkout.spec.ts` + POM; run `make e2e-critical`.
  Not on default Frontend CI. Option B (Stripe CLI full confirm) remains optional/local.
- **td-11:** Render cron `zeeframe-booking-lifecycle` + Procfile worker fallback.

## Suggested execution order

```
P1 — done (td-01, td-03)
Wave 3 hygiene — done (td-02 leftover A→E except payment/repository; td-04 done)

P2 (next):
  td-05 → td-06 → optional payment/repository split

P3 (remaining / anytime):
  td-07, td-08
  td-01, td-03, td-04, td-09, td-10, td-11 — done
```

## Growth items (not in this pack — future ADR)

- Redis cache for `get_studio_public` (Phase B, ~10k MAU)
- Read replica for `search` module
- Platform `application_fee` / take-rate writer (FR-04 deferred piece)

See architecture review discussion for rationale.
