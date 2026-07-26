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

- [x] STRATEGY.md — decisions resolved, stories prioritised, URL   tree agreed
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
- [x] `shared/auth`: `useAuth`, `useRole`, `usePermission`, `RequireAuth`, `RequireStudioRole`
- [x] `PermissionGate` component
- [x] TanStack Query provider + query key conventions
- [x] Global toast for transient errors; error boundary per route group

## Phase 3 — Storefront + booking + payment (P0 stories 1, 2)

Public zone first: simplest auth-wise, demoable to studios, closes the money loop.

- [x] `entities/studio` ui: StudioHeader, StudioGallery; `entities/service`: ServicePolaroidCard
- [x] `entities/occurrence`: OccurrenceRow, CapacityIndicator
- [x] `app/(main)/s/[slug]` on `GET /studios/slug/{slug}/public` (mobile-first)
- [x] `features/book-occurrence`: wizard (slot → guest form or sign-in → summary → Stripe)
- [x] Success page with webhook polling ("Payment processing…")
- [x] Guest confirm page `/bookings/{id}/confirm` via `access_token`
- [x] Edge cases: occurrence full, pending timer, webhook delayed
- [x] Playwright: guest checkout flow (update existing spec to slug routes)

## Phase 4 — Customer account (P0 stories 2, 5)

- [x] `entities/booking` ui: BookingCard, BookingStatusBadge, timeline
- [x] `app/(account)/bookings`: upcoming / past / cancelled (paginated via envelope)
- [x] `features/cancel-booking` with `cancel_before_hours` cutoff logic
- [x] `features/manage-account`: profile (PATCH /auth/me)
- [x] `app/(account)/orders`: course orders list
- [x] Edge cases: cancelled-by-studio, expired booking
- [x] Migrate old `/bookings` pages, set up redirects

## Phase 5 — Studio dashboard (P0 stories 3, 4)

Hardest zone — last, when the FSD pattern is routine.

**MVP decision (2026-07-26):** dual-persona mode switch ("Customer ↔ Studio {name}")
is **deferred**. One account can still be staff and customer in the API, but UX keeps
surfaces separate — simple cross-links only (`Account` ↔ `Dashboard`), never mixed nav.
Full mode switch → P1/polish when real cross-over demand appears.

- [x] `app/(dashboard)`: sidebar layout + StudioSwitcher + Account cross-link
- [x] `(account)` header: Dashboard cross-link when the user has a studio role
- [x] `/dashboard`: my studios list + onboarding funnel state (what's the next step)
- [x] `features/manage-studio`: create/edit profile, slug, timezone, cancel policy
- [x] `features/manage-services`: CRUD + VisibilityBadge (draft/published/archived tabs)
- [x] `features/manage-schedule` — **two separate sections**
  - [x] Templates (+ generate + warning) — `/dashboard/studios/{id}/services/{sid}/schedule`
  - [x] Calendar (list by date, edit/cancel with reason) — `/dashboard/studios/{id}/calendar`
- [x] Studio "Today" screen: sessions, booked/capacity/pending counters, quick actions
- [x] `/dashboard/studios/{id}/bookings` with filters
- [x] Permission-driven navigation (instructor sees reduced menu)

## Phase 6 — P1 stories

- [ ] Course booking wizard (order checkout, availability warnings)
- [ ] Stripe Connect onboarding + payouts status
- [ ] `features/check-in`: participants list + check-in / no-show (mobile-first)
- [ ] Team members management (invite manager/instructor)

## Later (P2 backlog)

Search/filters on `/studios` · week-view calendar · GDPR export/delete ·
"Add to calendar" · i18n (RU) — see STRATEGY §5.
