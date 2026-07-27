# Closed-beta production checklist (Wave 0)

Operator runbook for a small closed beta (1–3 studios) with **live** Stripe and Resend.
Variable names only — never commit real values. See `backend/.env.example` and
`frontend/.env.example` for descriptions.

## Before first studio goes live

### API (Render `zeeframe-api`)

- [ ] `ENVIRONMENT=production`
- [ ] `DATABASE_URL` — managed Postgres (not the local default)
- [ ] `SECRET_KEY` — strong unique value (Blueprint may `generateValue`)
- [ ] `FRONTEND_URL` — exact web origin, no trailing slash
- [ ] `CORS_ORIGINS` — same web origin (comma-separated if more than one)
- [ ] Rate limit: `REDIS_URL` **or** `ALLOW_INMEMORY_RATE_LIMIT=true` (single API instance only)
- [ ] `METRICS_TOKEN` — if you will scrape `/metrics`
- [ ] `TRUSTED_PROXY_IPS` — set only after confirming Render edge peer; empty = peer IP only

### Cron (Render `zeeframe-booking-lifecycle`)

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

## Do not

- Commit `.env`, dashboard screenshots with secrets, or live keys in docs/PRs
- Point production webhooks at localhost or Stripe **test** secrets
- Run multiple API replicas with only `ALLOW_INMEMORY_RATE_LIMIT=true`

## Quick health after deploy

- [ ] `GET /health` (and readiness if used) OK on API
- [ ] Sign-in OTP works end-to-end
- [ ] One paid booking confirms within a few minutes of Checkout
- [ ] Cron log appears at least once every ~5 minutes UTC
