# ADR-001: Date/Time Policy — Studio Local + UTC Instants

**Status:** Implemented  
**Date:** 2026-06-12  
**Context:** ZeeFrame — international SaaS for studio booking. Development stage allows full database rebuild.

## Context

The backend previously mixed three time representations:

- PostgreSQL `TIMESTAMPTZ` columns in ORM models
- Python naive UTC (`to_naive_utc`) for slot writes and filters
- Python aware UTC for auth, bookings, and tokens

Schedule templates use `date` + `time` without timezone, which was implicitly interpreted as UTC. That is incorrect for a multi-region product where "Monday 18:00" means local studio time.

We are rebuilding the database from scratch. This ADR replaces the interim "naive UTC" policy documented in `ARCHITECTURE_IMPROVEMENTS_PLAN.md` §3.2.

## Decision

### 1. Three semantic types

| Type | Storage | Python | Usage |
|------|---------|--------|-------|
| **Instant** | `TIMESTAMPTZ` | `datetime` aware, `tzinfo=UTC` | Slots, bookings, tokens, audit fields |
| **Calendar date** | `DATE` | `date` | Schedule `valid_from` / `valid_to`; date filters in studio-local context |
| **Wall-clock** | `TIME` | `time` | Schedule `start_time` — interpreted in studio timezone |

### 2. Studio timezone

Add `studios.timezone` (IANA identifier, e.g. `Europe/Berlin`, `America/New_York`).

- Represents the **business location timezone** for schedule templates and display.
- Validated at the API boundary via `zoneinfo.ZoneInfo`. Invalid identifier → HTTP 422.
- **Immutable after the studio has at least one slot** (MVP rule). Changing timezone post-factum requires a separate ADR and migration tooling.

#### Onboarding vs database default

| Context | Rule |
|---------|------|
| **Database column** | `NOT NULL DEFAULT 'UTC'` — technical fallback for dev, tests, and direct SQL inserts only |
| **Studio creation API (`StudioCreate`)** | `timezone` is **required**. No silent default. Client must send an explicit IANA timezone |
| **Studio update API** | Changing `timezone` is blocked once the studio has slots (MVP) |
| **Production expectation** | A studio in Berlin must be created with `timezone=Europe/Berlin`. Relying on the DB default in production is a configuration error |

WHY: `DEFAULT 'UTC'` in PostgreSQL prevents nullable-column edge cases during development; it must never substitute for an explicit owner choice at onboarding.

### 3. Conversion rules

- **ScheduleTemplate → Occurrence:** `studio_local_to_utc(date, time, studio.timezone)` → store as UTC instant.
- **API input (instant):** MUST include timezone offset or `Z`. Naive datetimes → HTTP 422 (no silent UTC conversion).
- **API output (instant):** ISO 8601 UTC with `Z` suffix.
- **API output (studio):** include `timezone` field; frontend converts instants for display.
- **Server clock:** always `utc_now()` from `app.core.datetime_utils`.

### 4. Forbidden patterns

- `datetime.utcnow()` (deprecated; easy to reintroduce by habit)
- `date.today()` for business logic — use `utc_now().date()` or `studio_local_date_now(tz_name)`
- `dt.replace(tzinfo=None)` / `to_naive_utc`
- Comparing aware and naive datetimes

### 5. `datetime_utils.py` public API

```python
def utc_now() -> datetime:
    """Current instant as aware UTC."""

def ensure_utc(dt: datetime) -> datetime:
    """Normalize input to aware UTC. Raises ValidationError on naive input."""

def studio_local_to_utc(d: date, t: time, tz_name: str) -> datetime:
    """Combine studio-local calendar date + wall-clock → UTC instant."""

def studio_local_date_now(tz_name: str) -> date:
    """Today's calendar date in the studio timezone."""
```

DST edge cases (`AmbiguousTimeError`, `NonExistentTimeError`) surface as HTTP 422 with a clear message.

### 6. Pending booking holds (`reserved_until`)

Keep the column. Implement TTL on create:

| Event | `reserved_until` |
|-------|------------------|
| Booking created (`status=pending`) | `utc_now() + PENDING_HOLD_TTL` |
| Booking confirmed or cancelled | `NULL` |
| Capacity check | existing `_pending_holds_capacity`: `reserved_until IS NOT NULL AND reserved_until > utc_now()` |

WHY: `_pending_holds_capacity` already implements the correct model. Removing the column now means re-adding it when real users abandon incomplete checkouts.

`PENDING_HOLD_TTL` lives in settings (env-configurable).

### 7. Database rebuild

- Drop and recreate the database (development only).
- Replace incremental Alembic history with a single initial migration containing `TIMESTAMPTZ` + `studios.timezone` from day one.
- No data migration scripts required.

## Implementation order

1. ADR accepted (this document)
2. Drop DB; squash Alembic to one initial migration
3. Models + Pydantic schemas (`Studio.timezone` required on create)
4. `datetime_utils.py` — new API; delete `to_naive_utc`
5. **Unit tests for `studio_local_to_utc` including DST** ← immediately after step 4, before seeds
6. Services, repositories, API layer
7. Wire `reserved_until` TTL on booking create
8. Update seeds (multi-TZ studios, slots via `studio_local_to_utc`)
9. Integration / API tests
10. Update `ARCHITECTURE_IMPROVEMENTS_PLAN.md` §3.2

WHY: DST bugs are only found by tests. Discover them before seeds populate the database with wrong instants.

## Consequences

### Positive

- Correct multi-timezone behavior for international studios.
- Single Python representation for instants (aware UTC).
- No silent timezone bugs from naive/aware mixing.
- Clean foundation for frontend i18n (display in studio or user TZ).
- Pending holds prevent abandoned checkouts from locking capacity indefinitely.

### Negative / trade-offs

- Frontend must receive `studio.timezone` to show local times.
- DST transitions require explicit test coverage and 422 handling.
- Studio timezone is immutable after first slot in MVP.
- Onboarding UX must include an explicit timezone picker (cannot rely on DB default).

## Alternatives considered

**A. Everything in UTC (naive or aware):** simpler but wrong UX for "Monday 18:00 class" — rejected.

**B. Store slots in studio local time:** breaks ordering, DST, and cross-studio queries — rejected.

**C. Keep `to_naive_utc` with TIMESTAMPTZ:** preserves old hack; contradicts ORM column types — rejected.

**D. Remove `reserved_until`:** would require re-adding when checkout abandonment becomes visible in production — rejected.

## References

- `backend/app/core/datetime_utils.py`
- `backend/app/models/studio.py`, `slot.py`, `schedule.py`, `booking.py`
- `backend/app/core/repositories/booking_repo.py` — `_pending_holds_capacity`
