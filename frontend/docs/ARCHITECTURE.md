# ZeeFrame Frontend — ARCHITECTURE

> How the frontend is built technically. Written for yourself three months from now.
> Product decisions live in [STRATEGY.md](./STRATEGY.md), API contracts in [CONTRACTS.md](./CONTRACTS.md).

## 1. Methodology: simplified FSD (3 layers)

```text
app/        → routing, layouts, page composition (Next.js App Router)
features/   → user actions with business logic (book-occurrence, cancel-booking, manage-services)
entities/   → domain objects: types, models, base UI, API hooks (studio, service, occurrence, booking, order, user)
shared/     → zero domain knowledge: api client, auth, ui kit, lib
```

### Dependency rule (enforced by ESLint)

```text
app → features → entities → shared
```

- Lower layers **never** import from higher layers.
- **Features never import other features.** Shared logic goes down to `entities/` or `shared/`.
- `app/` contains no business logic — only composition of features and entities.

## 2. Route groups

```text
src/app/
├── (main)/            → public: landing, /studios, /s/[slug], booking flow
├── (account)/         → customer account, guarded by RequireAuth
├── (dashboard)/       → studio dashboard, guarded by RequireAuth + studio role
└── auth/              → login / verify (no group — own minimal layout)
```

Each group owns its layout: public header for `(main)`, account nav for `(account)`,
sidebar + StudioSwitcher for `(dashboard)`.

## 3. Server Components strategy

The token model dictates the strategy — this is a constraint, not a preference:

- Access token lives **in client memory** (`shared/auth/storage`), never in cookies.
- Refresh token is an httpOnly cookie on the **API origin**, not the Next.js origin.
- Therefore the Next.js server (RSC, middleware, route handlers) **cannot authenticate
  a user**. Server-side data fetching is possible only for public endpoints.

| Zone | Rendering | Data fetching |
|------|-----------|---------------|
| `(main)` — landing, `/studios`, `/s/[slug]` | Server Components | server `fetch` to public API with `next: { revalidate }`; SEO via `generateMetadata` |
| Booking wizard, forms, any interactivity | Client islands inside RSC pages | TanStack Query mutations |
| `(account)`, `(dashboard)` | RSC shell (layout markup only), all data client-side | TanStack Query + `shared/api` client |

Rules that follow:

- `shared/api/client.ts` is **client-only** (mark with `import "client-only"`). Server
  components never import it.
- Public server-side fetching goes through a thin `shared/api/server.ts` helper:
  no auth, typed by the same generated OpenAPI types, used only in `(main)` pages.
- Route protection is **client-side** (`RequireAuth` / `RequireStudioRole` render a
  skeleton while checking). Next.js middleware cannot guard by auth — do not try.
- Consequence: server-rendered public pages carry zero personalization (correct for
  SEO and caching); anything user-specific renders as a client island.
- Cache defaults: landing — static; storefront `/s/[slug]` — `revalidate: 60`
  (capacity/availability numbers may be up to a minute stale; the booking wizard
  re-validates via client API on open).

## 4. Target directory layout

```text
src/
├── app/                        # routing only
├── features/
│   ├── book-occurrence/        # ui/ + model/ + api.ts + index.ts (public API of the feature)
│   ├── cancel-booking/
│   ├── manage-account/
│   ├── manage-studio/
│   ├── manage-services/
│   ├── manage-schedule/
│   ├── check-in/
│   └── auth/
├── entities/
│   ├── studio/                 # ui/ (StudioCard, StudioHeader), model/ (types, hooks), api.ts
│   ├── service/                # ServicePolaroidCard, VisibilityBadge
│   ├── occurrence/             # OccurrenceRow, CapacityIndicator
│   ├── booking/                # BookingCard, BookingStatusBadge
│   ├── order/
│   └── user/
└── shared/
    ├── api/                    # client.ts, types.generated.ts (OpenAPI), index.ts
    ├── auth/                   # context, storage, useAuth/useRole/usePermission, guards
    ├── ui/                     # Button, Card, Input, Badge, Tabs, Skeleton, Alert…
    └── lib/                    # utils, config, constants (single source of truth for statuses)
```

Domain components that appear on multiple surfaces live in `entities/`, not in a feature:
`PermissionGate`, `CapacityIndicator`, `VisibilityBadge`, `StudioSwitcher`,
`BookingStatusBadge`, `ServicePolaroidCard`, `OccurrenceRow`.

## 5. Migration map (current code → FSD)

| Current | Target |
|---------|--------|
| `src/lib/api/*` | `shared/api/` (+ generated types replace `src/types/*`) |
| `src/lib/auth*`, `src/context/*` | `shared/auth/` |
| `src/components/ui/*` | `shared/ui/` |
| `src/lib/utils.ts`, `config.ts` | `shared/lib/` |
| `src/types/*` (hand-written) | **deleted** — replaced by `types.generated.ts` + entity models |
| `src/features/home`, `navigation` | stay as features (landing untouched) |
| `src/features/studios` | split: cards → `entities/studio`, search → `features/search-studios` |
| `src/app/(main)/studios/[id]` (public) | `app/(main)/s/[slug]` on public API |
| `src/app/(main)/bookings/*` (account list) | `app/(account)/account/bookings` (`/account/bookings`; exact `/bookings` redirects) |
| `src/app/(main)/dashboard/*` | `app/(dashboard)/…` sidebar + sub-routes |
| `src/store/useUIStore.ts` | keep only if actually used; prefer local state |

## 6. Stack (locked)

| Concern | Choice | Notes |
|---------|--------|-------|
| Framework | Next.js App Router | Server Components by default, `'use client'` only when needed |
| Server state | TanStack Query | one `QueryClient` in providers; keys per entity |
| UI state | `useState` / `useReducer` locally | Zustand only if a real global need appears |
| Forms | React Hook Form + Zod | schemas in `features/*/model` or `shared/lib/schemas` |
| API types | `openapi-typescript` | generated from FastAPI `/openapi.json`, committed |
| Styling | Tailwind v4 (existing tokens: mint/navy, polaroid) | |
| Unit tests | Vitest | |
| E2E | Playwright (`e2e/`, POM pattern) | critical flows only |
| Lint | ESLint + boundary rule between FSD layers | |

## 7. Type generation from OpenAPI

- Source of truth: backend `/openapi.json`.
- `npm run generate:api` → `shared/api/types.generated.ts` (committed to git for reviewable diffs).
- Hand-written API types are forbidden. Entity models may **narrow** or **compose**
  generated types, never redefine them.
- Statuses are consumed via constants in `shared/lib/constants.ts`
  (`BookingStatus.CONFIRMED`, not the string `'confirmed'`).

## 8. Auth and permissions on the frontend

- `GET /auth/me` returns the user **plus** `roles: [{studio_id, role}]` — the frontend builds
  navigation and route guards from this single response.
- `shared/auth` exposes:
  - `useAuth()` — user, tokens, login/logout
  - `useRole(studioId)` — studio role of the current user
  - `usePermission(studioId)` — `can('manage_schedule')` mirrors the backend
    `STUDIO_PERMISSIONS_BY_ROLE` matrix (see CONTRACTS §2); the matrix is copied into
    `shared/lib/constants.ts` and must be kept in sync with the backend
  - Guards: `RequireAuth`, `RequireStudioRole`; UI gate: `PermissionGate` (in `entities/user` or `shared/auth`)
- The frontend gate is UX-only; the backend enforces permissions server-side.

## 9. Backend module → frontend entity mapping

| Backend module | Frontend entity / feature |
|----------------|---------------------------|
| `catalog/studio` | `entities/studio`, `features/manage-studio` |
| `catalog/service` | `entities/service`, `features/manage-services` |
| `catalog/occurrence` + `schedule` | `entities/occurrence`, `features/manage-schedule` |
| `catalog/public` | storefront pages (`app/(main)/s/[slug]`) |
| `booking` | `entities/booking`, `features/book-occurrence`, `features/cancel-booking`, `features/check-in` |
| `booking/order` | `entities/order` |
| `payment` | checkout step inside `features/book-occurrence`; payouts (P1) |
| `auth` | `shared/auth`, `features/auth`, `features/manage-account` |
| `search` | `features/search-studios` |

## 10. Error handling

- API client parses RFC 7807 Problem JSON (`{type, title, status, detail, request_id}`)
  into a typed `ApiError`.
- Global toast for transient errors; error boundaries per route group.
- Raw `detail` is never shown to users verbatim — map by `status` (+ context) to friendly copy.
- `X-Request-ID` from responses is attached to error reports/logs for end-to-end tracing.
