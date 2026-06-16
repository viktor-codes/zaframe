# TD-07 — Documentation cleanup (P3)

> Read [README.md](./README.md). Docs-only step — no runtime behaviour change.

## Problem

1. **Root `README.md`** still uses pre-ADR-002 vocabulary ("slots", "magic-link" vs OTP).
2. **`backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md`** references deleted `app.services`,
   `app.schemas` layout — misleading for new contributors.
3. **`docs/refactor/README.md`** status still reads like work-in-progress.

## Goal

Docs match the modular-monolith reality. Single source of truth for architecture:
`docs/ARCHITECTURE.md` + ADR-003.

## Tasks

### 1. Update root `README.md`

| Section | Change |
|---------|--------|
| "What it does" | `slots` → **occurrences**; `ScheduleTemplate` where relevant |
| Architecture diagram | `Services` → `modules/*` or annotate "domain modules" |
| Auth | "magic-link" → **email OTP** (accurate to implementation) |
| Engineering practices | Add bullet: modular monolith + `uv run lint-imports` |
| Link | Add `[Architecture](docs/ARCHITECTURE.md)` and `[ADR-003](docs/adr/003-modular-monolith.md)` |

Do **not** rewrite the whole README — surgical edits only.

### 2. Retire `backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md`

**Option A (recommended):** Delete file; add at top of `docs/ARCHITECTURE.md`:

```markdown
## Historical note
Pre-modular-monolith improvement notes lived in `backend/docs/ARCHITECTURE_IMPROVEMENTS_PLAN.md`
(superseded by ADR-003, 2026-06).
```

**Option B:** Keep file but add banner:

```markdown
> **SUPERSEDED** — see docs/ARCHITECTURE.md and docs/adr/003-modular-monolith.md. Do not follow.
```

### 3. Update `docs/refactor/README.md`

Add at top:

```markdown
**Status:** ✅ Completed (branch merged or ready to merge). See docs/tech-debt/ for follow-up work.
```

### 4. Update `docs/ARCHITECTURE.md` (if td-03 landed)

Ensure payment → identity edge is in the allowed-edges table.

## Definition of Done

```bash
rg "app\.services\.|slots tied to a studio schedule" README.md backend/docs
# → zero misleading hits (or only historical banners)
```

No pytest required; optional `make lint` if only markdown changed.

## Commit

```
docs: align README and retire stale architecture plan
```

## Out of scope

Frontend README; OpenAPI description strings.
