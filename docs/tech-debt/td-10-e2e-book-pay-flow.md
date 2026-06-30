# TD-10 — E2E: guest book → Stripe checkout → confirmed (P3)

> Read [README.md](./README.md). **Largest effort** (~1 day). Requires full stack running.

## Problem

`frontend/e2e/smoke.spec.ts` only checks page load. Critical revenue path untested:
discover studio → book occurrence → pay → booking confirmed.

## Goal

One Playwright **critical flow** test with Page Object Model, `data-testid` selectors,
Stripe test mode. Runnable locally via documented command; CI optional (flaky external deps).

## Preconditions

- Backend on `http://localhost:8000` (or env `API_URL`)
- Frontend `playwright.config.ts` `webServer` starts Next.js
- PostgreSQL with migrations applied
- Stripe test keys in backend `.env` (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`)
- Seed data: at least one studio with bookable occurrence OR test creates data via API

## Architecture

```
frontend/e2e/
├── flows/
│   └── guest-checkout.spec.ts
├── pages/
│   ├── studio-public.page.ts
│   ├── booking.page.ts
│   └── stripe-checkout.page.ts   # Stripe hosted page helpers
└── fixtures/
    └── api-seed.ts               # optional: create studio/occurrence via API
```

## Test scenario (happy path)

1. **Arrange** — seed via API (preferred) or use known seed slug from `tests.e2e.seed_and_simulate`:
   - Studio slug `test-yoga` (document actual slug in test constant)
   - Active occurrence with capacity > 0
2. **Act**
   - Navigate `/studios/{slug}` (or public route used by frontend)
   - Select occurrence → open booking form
   - Submit guest details (name, email, phone)
   - Receive `access_token` in response (intercept network OR poll API)
   - Click pay → redirect to Stripe Checkout (test mode)
   - Complete payment with Stripe test card `4242...`
   - Simulate webhook **OR** use Stripe CLI forwarding (see below)
3. **Assert**
   - Booking status `confirmed` via `GET /api/v1/bookings/{id}` with access token / auth
   - UI shows confirmation state (if applicable)

## Stripe webhook strategy

**Option A — API integration test hybrid (recommended for CI stability):**

E2E stops at Stripe redirect; separate backend test confirms webhook (already exists in
`test_webhooks.py`). E2E asserts `checkout.session` URL created and booking stays `pending`.

**Option B — Full E2E with Stripe CLI:**

```bash
stripe listen --forward-to localhost:8000/webhooks/stripe
```

Playwright test tagged `@slow` / `test.describe.configure({ mode: 'serial' })`.

Document in test file which mode is used. **Default deliverable: Option A** unless user
explicitly wants Option B.

## Frontend requirements

Add `data-testid` to critical elements (minimal set):

| Element | testid |
|---------|--------|
| Book button | `book-occurrence-button` |
| Guest email input | `guest-email-input` |
| Submit booking | `submit-booking-button` |
| Pay button | `pay-booking-button` |

Search existing components before adding — avoid duplicates.

## Playwright config updates

```typescript
// playwright.config.ts
webServer: [
  { command: "cd ../backend && uv run uvicorn app.main:app --port 8000", url: "http://127.0.0.1:8000/health" },
  { command: "npm run dev", url: baseURL },
],
```

Or document manual two-terminal workflow if multi-webServer is flaky on user's machine.

Add npm script:

```json
"test:e2e:critical": "playwright test e2e/flows/guest-checkout.spec.ts"
```

## Makefile (repo root)

```makefile
e2e:
	cd frontend && npm run test:e2e

e2e-critical:
	cd frontend && npm run test:e2e:critical
```

## Definition of Done

- `npm run test:e2e` — smoke + new flow pass locally (document env vars in `frontend/e2e/README.md` — **only if user approves new doc file**, else comment in spec file).
- Test uses `getByTestId`, not CSS classes.
- No hardcoded production secrets.

## Commit

```
test(web): add e2e guest checkout flow with page objects
```

## Out of scope

Course multi-booking order flow; authenticated user book; mobile viewport matrix.
