# ZeeFrame Frontend — ROADMAP

> In what order we build. Stories and edge cases in [STRATEGY.md](./STRATEGY.md),
> technical rules in [ARCHITECTURE.md](./ARCHITECTURE.md), API in [CONTRACTS.md](./CONTRACTS.md).

## Working agreements

- The landing page is **not touched** — it ships as-is.
- One phase = a sequence of small commits by FSD layer: entity → feature → app.
- A screen is done only when it passes the Definition of Done (below).
- API-first: before building a screen, verify the endpoint exists, matches CONTRACTS.md,
  and is covered by generated types. Never build on mocks that will drift.

### Git — human commits only (mandatory)

After **every** finished roadmap chunk (one checklist item or one agreed sub-step):

1. The agent **never** runs `git commit` / `git push` unless the human explicitly asks.
2. The agent ends the chunk with a ready-to-paste **Conventional Commit** message
   (`feat(web): …`, `refactor(web): …`, `chore(web): …`, `test(web): …`).
3. The human commits locally by hand (and pushes when ready).
4. Next chunk starts only after the human confirms the previous commit (or says to continue).

## Definition of Done (every screen)

```text
[ ] loading state
[ ] error state (Problem JSON → friendly message)
[ ] empty state (JTBD copy + CTA)
[ ] mobile verified
[ ] edge cases from STRATEGY §7 covered
[ ] types generated from OpenAPI, no hand-written API types
```

---

## Phase 0 — Fixation (done 2026-07-05)

- [x] STRATEGY.md — decisions resolved, stories prioritised, URL tree agreed
- [x] ARCHITECTURE.md — FSD layers, stack, migration map
- [x] CONTRACTS.md — roles, permissions, statuses, errors, endpoints
- [x] ROADMAP.md — this file

**External blockers to schedule with backend:**

- [x] Pagination envelope `{items, total, page, size}` (blocks Phase 4–5 list screens)
- [x] FR-12 stabilization pack (blocks Phase 3 payments happy path in prod)

## Phase 1 — FSD refactoring (no new features)

One commit per step, history stays readable:

- [x] 1. Create `shared/`, `entities/`, `features/` skeleton + tsconfig path aliases
- [x] 2. `shared/api`: move client, set up `openapi-typescript` generation (`npm run generate:api`)
- [x] 3. `shared/auth`: context, storage, types
- [x] 4. `shared/ui`: move UI kit components (no business logic inside)
- [x] 5. `entities/` for studio, service, occurrence, booking, order, user — types + base models only
- [x] 6. Move `features/auth`
- [x] 7. Route groups: `(main)` / `(account)` / `(dashboard)` with own layouts
- [x] 8. ESLint boundary rule for FSD layers
- [x] 9. Delete dead assets from `public/` and unused hand-written types

## Phase 2 — Shared foundation

- [x] `shared/api/client.ts` (client-only): auth headers, refresh, `ApiError` (RFC 7807), `X-Request-ID`, Idempotency-Key helper
- [x] `shared/api/server.ts`: unauthenticated server fetch for public endpoints (RSC, see ARCHITECTURE §3)
- [x] `shared/lib/constants.ts`: all statuses + permissions matrix (single source of truth)
- [ ] `shared/auth`: `useAuth`, `useRole`, `usePermission`, `RequireAuth`, `RequireStudioRole`
- [ ] `PermissionGate` component
- [ ] TanStack Query provider + query key conventions
- [ ] Global toast for transient errors; error boundary per route group

## Phase 3 — Storefront + booking + payment (P0 stories 1, 2)

Public zone first: simplest auth-wise, demoable to studios, closes the money loop.

- [ ] `entities/studio` ui: StudioHeader, StudioGallery; `entities/service`: ServicePolaroidCard
- [ ] `entities/occurrence`: OccurrenceRow, CapacityIndicator
- [ ] `app/(main)/s/[slug]` on `GET /studios/slug/{slug}/public` (mobile-first)
- [ ] `features/book-occurrence`: wizard (slot → guest form or sign-in → summary → Stripe)
- [ ] Success page with webhook polling ("Payment processing…")
- [ ] Guest confirm page `/bookings/{id}/confirm` via `access_token`
- [ ] Edge cases: occurrence full, pending timer, webhook delayed
- [ ] Playwright: guest checkout flow (update existing spec to slug routes)

## Phase 4 — Customer account (P0 stories 2, 5)

- [ ] `entities/booking` ui: BookingCard, BookingStatusBadge, timeline
- [ ] `app/(account)/bookings`: upcoming / past / cancelled (paginated via envelope)
- [ ] `features/cancel-booking` with `cancel_before_hours` cutoff logic
- [ ] `features/manage-account`: profile (PATCH /auth/me)
- [ ] `app/(account)/orders`: course orders list
- [ ] Edge cases: cancelled-by-studio, expired booking
- [ ] Migrate old `/bookings` pages, set up redirects

## Phase 5 — Studio dashboard (P0 stories 3, 4)

Hardest zone — last, when the FSD pattern is routine.

- [ ] `app/(dashboard)`: sidebar layout + StudioSwitcher + header mode switch (Customer ↔ Studio)
- [ ] `/dashboard`: my studios list + onboarding funnel state (what's the next step)
- [ ] `features/manage-studio`: create/edit profile, slug, timezone, cancel policy
- [ ] `features/manage-services`: CRUD + VisibilityBadge (draft/published/archived tabs)
- [ ] `features/manage-schedule`: **two separate sections** — Templates (+ generate + warning) and Calendar (list by date, edit/cancel with reason)
- [ ] Studio "Today" screen: sessions, booked/capacity/pending counters, quick actions
- [ ] `/dashboard/studios/{id}/bookings` with filters
- [ ] Permission-driven navigation (instructor sees reduced menu)

## Phase 6 — P1 stories

- [ ] Course booking wizard (order checkout, availability warnings)
- [ ] Stripe Connect onboarding + payouts status
- [ ] `features/check-in`: participants list + check-in / no-show (mobile-first)
- [ ] Team members management (invite manager/instructor)

## Later (P2 backlog)

Search/filters on `/studios` · week-view calendar · GDPR export/delete ·
"Add to calendar" · i18n (RU) — see STRATEGY §5.
