# TD-08 — Merge preparation checklist (P3)

> Read [README.md](./README.md). **Process step** — minimal or no code. Run before merging
> `refactor/modular-monolith` → `main`.

## Goal

Clean, reviewable merge suitable for portfolio: green CI, coherent history, PR description
ready to paste.

## Checklist (agent executes and reports)

### 1. Quality gates

```bash
cd backend && uv run ruff check .
cd backend && uv run lint-imports
cd backend && uv run pytest -q
cd frontend && npm run build
cd frontend && npm run test  # if vitest configured
```

All must pass. Record counts (tests, contracts).

### 2. Branch hygiene

```bash
git fetch origin
git log origin/main..HEAD --oneline
git diff origin/main --stat
```

- Confirm **no** `.env`, secrets, or `uv.lock` surprises unintended.
- List commits for PR description (12 refactor + tech-debt if any).

### 3. Optional: fix commit typo

Commit `6bb5767` message reads `efactor(booking)` — missing `r`.

**Only if branch not pushed / not shared:**

```bash
git rebase -i 6bb5767^
# reword → refactor(booking): move booking + order into modules/booking, add policies
```

**If already pushed:** leave history OR add empty note in PR body — do **not** force-push
without explicit user approval.

### 4. PR description template

Agent fills and saves to `docs/tech-debt/MERGE_PR_BODY.md`:

```markdown
## Summary
- Modular monolith: domain modules under `app/modules/`, shared `models/`, flat UoW
- Architecture guards: import-linter (7 contracts) + `tests/architecture/`
- No breaking API route changes

## Test plan
- [ ] `uv run pytest -q` (N passed)
- [ ] `uv run lint-imports` (7 kept)
- [ ] Manual smoke: studio public → book → OTP → pay (Stripe test)
- [ ] OpenAPI /docs unchanged paths

## ADR
- docs/adr/003-modular-monolith.md

## Follow-up (separate PRs)
- docs/tech-debt/ P1 items
```

### 5. Squash vs merge

**Recommend:** merge with merge commit (preserve 12-step history for portfolio) OR rebase
merge — **do not** squash entire refactor into one commit unless user requests (loses
narrative).

## Definition of Done

- `MERGE_PR_BODY.md` created.
- Checklist results documented in PR body or comment.
- User explicitly approves merge strategy.

## Commit (if only adding PR body)

```
docs: add modular-monolith merge PR template
```

## Out of scope

Actually merging to main; deploying production.
