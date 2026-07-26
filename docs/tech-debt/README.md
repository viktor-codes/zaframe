# Tech Debt Task Pack — Post Modular-Monolith Review

Companion to the architecture review after [ADR-003](../adr/003-modular-monolith.md) landed.
Each `td-NN-*.md` is one self-contained step for a coding agent.

**Baseline (must stay green after every step):**
```bash
cd backend && uv run ruff check . && uv run lint-imports && uv run pytest -q
```
Currently: **172 tests**, **7 import-linter contracts KEPT**.

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
| 🔴 P1 | [td-01](./td-01-catalog-capacity-dry.md) | DRY overbooking logic → `catalog/capacity.py` | ~3h |
| 🟡 P2 | [td-02](./td-02-split-large-services.md) | Split oversized services (payment/auth/studio done; booking TBD) | partial |
| 🔴 P1 | [td-03](./td-03-identity-ownership-policies.md) | Unify `is_own_booking` / `is_own_order` | ~2h |
| 🟡 P2 | [td-04](./td-04-split-studio-router.md) | Decompose `studio/router.py` god-router | ~3h |
| 🟡 P2 | [td-05](./td-05-booking-persistence-internal.md) | `booking/persistence.py` for intra-domain helpers | ~1.5h |
| 🟡 P2 | [td-06](./td-06-occurrence-bookings-count.md) | Relocate `get_bookings_count` from occurrence | ~1h |
| 🟢 P3 | [td-07](./td-07-docs-cleanup.md) | README vocabulary + retire stale plan doc | ~1h |
| 🟢 P3 | [td-08](./td-08-merge-prep.md) | PR checklist + optional history fix | ~30m |
| 🟢 P3 | [td-09](./td-09-pyright-ci.md) | Pyright strict in dev + CI/Makefile | ~4h |
| 🟢 P3 | [td-10](./td-10-e2e-book-pay-flow.md) | Playwright: guest book → pay → confirm | ~1d |
| ✅ Done | [td-11](./td-11-booking-lifecycle-cron.md) | Production cron for booking lifecycle | done |

## Suggested execution order

```
P1 (any order, but td-01 before td-02 catalog split):
  td-01 → td-03 → td-02

P2 (after P1):
  td-05 → td-06 → td-04   # td-05 before td-02 if booking split not done yet

P3 (parallel / anytime):
  td-07, td-09, td-11 independent
  td-10 needs running stack + Stripe test mode
  td-08 last — before merge to main
```

## Growth items (not in this pack — future ADR)

- Redis cache for `get_studio_public` (Phase B, ~10k MAU)
- `StudioMember` RBAC module
- Read replica for `search` module

See architecture review discussion for rationale.
