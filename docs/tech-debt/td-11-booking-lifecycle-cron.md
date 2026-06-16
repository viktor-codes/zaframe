# TD-11 — Production cron for booking lifecycle (P3)

> Read [README.md](./README.md).

## Problem

`scripts/run_booking_lifecycle.py` expires stale `pending` bookings and completes past
`confirmed` ones — but **nothing runs it in production** today (`Procfile` only starts
uvicorn). Without this, capacity leaks on abandoned checkouts and dashboards show stale
pending counts.

## Goal

Reliable scheduled execution every **5 minutes** in deployment environment, with logging
and idempotent behaviour (script already idempotent).

## Existing script

```bash
cd backend && uv run python -m scripts.run_booking_lifecycle
```

Calls `expire_stale_pending` + `complete_past_confirmed` in one `uow_scope()` transaction.

## Implementation options (pick based on host — agent documents choice)

### Option A — Railway / Render cron job (recommended for solo)

**Railway:** add Cron service:

```json
// railway.json or dashboard
{
  "cron": "*/5 * * * *",
  "command": "cd backend && uv run python -m scripts.run_booking_lifecycle"
}
```

**Render:** Background Worker with cron trigger in dashboard.

### Option B — Second Procfile process (if platform supports worker dyno)

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
release: cd backend && uv run alembic upgrade head
worker: cd backend && uv run python -m scripts.run_booking_lifecycle_loop
```

Add `scripts/run_booking_lifecycle_loop.py`:

```python
"""Run lifecycle every 5 minutes — for worker dyno only."""
import asyncio
import time

async def loop_forever():
    while True:
        await run_booking_lifecycle()
        await asyncio.sleep(300)
```

Use only if cron not available (less ideal — burns always-on worker).

### Option C — pg_cron (if DB hosted on Neon/Supabase with pg_cron)

SQL function calling HTTP health endpoint is **not** applicable — needs app context.
Skip unless using external scheduler hitting an internal endpoint.

### Option D — Protected HTTP endpoint (alternative)

Add `POST /internal/jobs/booking-lifecycle` secured by `INTERNAL_JOB_SECRET` header.
Cron hits endpoint via curl. **Only if** user prefers HTTP trigger — adds attack surface;
document in ADR if chosen.

**Default deliverable: Option A** + documentation.

## Steps

1. Document chosen approach in `docs/ARCHITECTURE.md` section **Background jobs**.
2. Add env var to `.env.example` if Option D:
   ```
   # INTERNAL_JOB_SECRET=required for /internal/jobs/* when using HTTP cron
   ```
3. Ensure script logs `booking_lifecycle_complete` with counts (already does).
4. Add lightweight test:

```python
# tests/unit/test_booking_lifecycle_script.py
async def test_run_booking_lifecycle_returns_tuple(monkeypatch):
    # mock expire_stale_pending / complete_past_confirmed
    ...
```

5. Update root `Makefile`:

```makefile
booking-lifecycle:
	cd backend && uv run python -m scripts.run_booking_lifecycle
```

## Monitoring

Log-based alert suggestion (document only, no Datadog required):

- If `expired_count` spikes > N per run → investigate payment funnel
- If script fails 3 runs → page owner

## Definition of Done

- Cron documented and configured for deployment target (or `booking-lifecycle` Make target
  for manual ops documented clearly).
- `uv run pytest -q` green.
- One dry-run locally prints expiry/completion counts.

## Commit

```
chore(ops): schedule booking lifecycle job every 5 minutes
```

## Out of scope

Celery/Redis queue; email reminders for expired bookings.
