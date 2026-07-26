# TD-11 — Production cron for booking lifecycle (P3) — DONE

> Read [README.md](./README.md).
>
> **Status:** Done (Jul 2026). Primary path is Render cron; Procfile worker is the fallback.

## Problem (resolved)

`scripts/run_booking_lifecycle.py` expires stale `pending` bookings and completes past
`confirmed` ones. Without a scheduler, capacity leaks on abandoned checkouts.

## Chosen approach

### Primary — Option A (Render cron)

Root `render.yaml` defines:

- Service: `zeeframe-booking-lifecycle`
- Schedule: `*/5 * * * *` (UTC)
- Command: `python -m scripts.run_booking_lifecycle`

### Fallback — Option B (Procfile worker)

For hosts that support a second process but not cron:

```
web: uvicorn ...
worker: python -m scripts.run_booking_lifecycle_loop
```

Loop script: `backend/scripts/run_booking_lifecycle_loop.py`  
Interval: `BOOKING_LIFECYCLE_INTERVAL_SECONDS` (default `300`).

## Ops

```bash
make booking-lifecycle
# or: cd backend && uv run python -m scripts.run_booking_lifecycle
```

Documented in `docs/ARCHITECTURE.md` → **Background jobs**.

## Definition of Done

- [x] Cron configured for deployment target (`render.yaml`)
- [x] Procfile worker fallback for non-cron hosts
- [x] Script logs `booking_lifecycle_complete` with counts
- [x] `make booking-lifecycle` available
- [x] Entrypoint unit test in `tests/integration/booking/test_booking_lifecycle_script.py`

## Commit (historical)

```
chore(ops): schedule booking lifecycle job every 5 minutes
```

## Out of scope

Celery/Redis queue; email reminders for expired bookings.
