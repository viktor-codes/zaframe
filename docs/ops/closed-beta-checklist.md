# Closed-beta / soft-launch production checklist

Operator runbook for a small closed beta (1–3 studios) with **live** Stripe and Resend,
plus Wave 1 soft-launch observability. Variable names only — never commit real values.
See `backend/.env.example` and `frontend/.env.example` for descriptions.

## Before first studio goes live

### API (Render `zeeframe-api`)

- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL` — managed Postgres (not the local default)
- [ ] `SECRET_KEY` — strong unique value (Blueprint may `generateValue`)
- [ ] `FRONTEND_URL` — exact web origin, no trailing slash
- [ ] `CORS_ORIGINS` — same web origin (comma-separated if more than one)
- [ ] Rate limiting — see § Rate limiting below (Redis preferred)
- [ ] `METRICS_TOKEN` — if you will scrape `/metrics`
- [ ] `TRUSTED_PROXY_IPS` — set only after confirming Render edge peer; empty = peer IP only

### Rate limiting (production recommendation)

**Prefer Redis.** SlowAPI counters must be shared across API processes. Without
`REDIS_URL`, each instance keeps its own in-memory counters (OTP/refresh/checkout
limits weaken under scale).

| Mode | When | Env |
|------|------|-----|
| **Recommended** | Any paid / multi-instance deploy | `REDIS_URL` set; `ALLOW_INMEMORY_RATE_LIMIT=false` (or unset) |
| **Closed-beta escape hatch** | Single free `zeeframe-api` instance only | `ALLOW_INMEMORY_RATE_LIMIT=true`; leave `REDIS_URL` empty |

Local / `ENVIRONMENT=dev`: leave both unset — in-memory is fine for one process.

**Upgrade path (Render Key Value):**

1. Create a Key Value instance (Blueprint snippet at bottom of `render.yaml`, or Dashboard → New → Key Value). Plan is paid (`starter`+); not on free Blueprint.
2. Wire `REDIS_URL` from the instance `connectionString` (`fromService` type `keyvalue`).
3. Set `ALLOW_INMEMORY_RATE_LIMIT=false` (or remove the var) on `zeeframe-api`.
4. Redeploy; confirm startup succeeds without the in-memory warning log
   (`production_inmemory_rate_limit_allowed`).
5. Keep a **single** API instance until Redis is live — never scale replicas on the escape hatch.

- [ ] Decision recorded: Redis **or** documented single-instance escape hatch
- [ ] If Redis: `REDIS_URL` set; escape hatch off
- [ ] If escape hatch: exactly one API instance; no horizontal scale

### Cron (Render `zeeframe-booking-lifecycle`)

- [ ] `ENVIRONMENT=production` — Blueprint sets this (parity with web; Settings default is `dev`)
- [ ] `DATABASE_URL` — same DB as API
- [ ] `SECRET_KEY` — synced from `zeeframe-api` via Blueprint `fromService`
- [ ] After deploy: Trigger Run once; log shows `booking_lifecycle_complete`

### Email (Resend)

- [ ] `RESEND_API_KEY` — live key
- [ ] `EMAIL_FROM` — verified domain sender (not a placeholder inbox)
- [ ] Smoke: request OTP for a real inbox; code arrives; no OTP plaintext in API logs

### Payments (Stripe live)

- [ ] `STRIPE_SECRET_KEY` — `sk_live_…` (not test)
- [ ] `STRIPE_WEBHOOK_SECRET` — signing secret for the **production** webhook endpoint
- [ ] Webhook URL points at the API host `/webhooks/…` (outside Next rewrite)
- [ ] Studio has completed Connect onboarding (`stripe_account_id` + charges enabled)
- [ ] Smoke: guest book → Checkout → pay → booking/order confirmed after webhook

### Web (Vercel / Next)

- [ ] `NEXT_PUBLIC_API_URL` — **web origin** (same-site `/api` + cookies), not the raw API host
- [ ] `API_UPSTREAM_URL` — FastAPI origin for rewrites / RSC (server-only)
- [ ] Studio `cover_url` / `logo_url` (https) render without CSP console errors
- [ ] `NEXT_PUBLIC_SENTRY_DSN` — browser/server Sentry project (optional until soft-launch)

### Observability (Sentry)

- [ ] API `SENTRY_DSN` set on Render `zeeframe-api`
- [ ] Web `NEXT_PUBLIC_SENTRY_DSN` set on Vercel
- [ ] Trigger a test error (or Sentry “Send test event”); event appears in the project
- [ ] Confirm no OTP codes / Stripe secrets in event payloads

## Do not

- Commit `.env`, dashboard screenshots with secrets, or live keys in docs/PRs
- Point production webhooks at localhost or Stripe **test** secrets
- Run multiple API replicas with only `ALLOW_INMEMORY_RATE_LIMIT=true`

## Quick health after deploy

- [ ] `GET /health` (and readiness if used) OK on API
- [ ] Sign-in OTP works end-to-end
- [ ] One paid booking confirms within a few minutes of Checkout
- [ ] Cron log appears at least once every ~5 minutes UTC

## Uptime check (Wave 1)

External ping only — no app code required. Pick one provider in the dashboard
(UptimeRobot, Better Stack, Cloudflare Health Checks, Render health checks, etc.).

- [ ] Monitor `GET {API_PUBLIC_URL}/health` (or `/api/v1/health` if that is the public path)
- [ ] Interval 1–5 minutes; alert on failure (email and/or Slack)
- [ ] Confirm one intentional fail (stop API briefly or block the check) triggers an alert
- [ ] Document the public health URL in the team runbook (not in git secrets)

## Postgres backups + restore drill (Wave 1)

Use the managed database provider (Render Postgres / Neon / etc.). Do not store
dump files or credentials in the repo.

- [ ] Automatic backups enabled on the production database
- [ ] Retention meets your RPO (e.g. ≥ 7 daily backups for closed beta)
- [ ] **Restore drill (once):** create a temporary restore from the latest backup →
      point a throwaway API instance (or local) at it → `GET /health` OK →
      run one read query (e.g. count users) → tear down the restored instance
- [ ] Note the date of the last successful restore drill in the ops log (outside git)
