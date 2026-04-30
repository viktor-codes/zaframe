# ZaFrame — Project analysis and frontend work phases

## 1. Current state analysis

### 1.1 Backend (context for the frontend)

- **Stack**: FastAPI, SQLAlchemy 2, Pydantic v2, uv
- **API**: versioned `/api/v1/`
  - **auth** — Magic Link (request, verify, refresh)
  - **studios** — CRUD, public studio profile
  - **services** — studio services, courses, availability
  - **slots** — slots (schedule)
  - **bookings** — create/cancel bookings
  - **payments** — Stripe Checkout (single/course)
  - **webhooks** — Stripe webhooks

Domain: studios (photo/video), services, slots, bookings, payment, studio owners, guests (no account).

### 1.2 Frontend (what already exists)

| Area | Status |
|------|--------|
| **Framework** | Next.js 16 (App Router), React 19 |
| **Language** | TypeScript |
| **Styles** | Tailwind CSS 4, custom theme in `globals.css` (mint/navy, polaroid) |
| **Data** | TanStack React Query v5 |
| **Fonts** | Inter, Montserrat (next/font) |
| **Pages** | Home, studio list/card, slot booking, booking list, confirm/cancel/success, owner dashboard (studio CRUD), auth (login, verify) |
| **Components** | Header, RequireAuth, UI kit: Button, Card, Input, Textarea, Alert, Badge, Skeleton |
| **Types** | auth, booking, payment, slot, studio, user (aligned with backend) |

### 1.3 Gaps identified

- **Missing `src/lib` folder**: the code references `@/lib/auth` (AuthProvider, useAuth) and `@/lib/api` (fetchStudio, createBooking, ApiError, requestMagicLink, verifyMagicLink, etc.). Without these modules, the frontend build/run will fail. Add `lib/auth` and `lib/api` in the first phase.

---

## 2. Technology: what we use and what to add

### 2.1 Already chosen (keep as-is)

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.x | App Router, RSC, API routes when needed |
| **React** | 19.x | UI |
| **TypeScript** | 5.x | Typing |
| **Tailwind CSS** | 4.x | Styles, design system |
| **TanStack Query** | 5.x | Cache, queries, mutations |
| **React Compiler** | (babel) | Render optimization (already in devDependencies) |

### 2.2 Recommended additions

| Technology | Purpose | Priority |
|------------|---------|----------|
| **zod** | Form validation and API response validation on the client | High |
| **React Hook Form** (optional) | Forms with minimal re-renders, easy zod integration | Medium |
| **Unified API client** | `src/lib/api` — single module with `baseURL`, 401/refresh handling, error types (ApiError) | High |
| **Token storage** | httpOnly cookie (if backend sets Set-Cookie) or secure in-memory storage + refresh; not localStorage for access token in production | High |
| **Testing** | Vitest + React Testing Library for unit/integration of components and hooks | Medium |
| **E2E** | Playwright (optional) for critical paths: studio → slot → booking → payment | Low |

### 2.3 What we avoid at this stage

- Heavy UI libraries (MUI, Ant) — a custom UI kit and design system already exist.
- Redux/MobX — TanStack Query + context (Auth) is enough for current state size.
- A separate form state manager — start with React state and add React Hook Form if needed.

### 2.4 Technology summary

- **Core**: Next.js 16, React 19, TypeScript, Tailwind 4, TanStack Query.
- **Add first**: `src/lib/api`, `src/lib/auth`, validation (zod), unified API client with CORS and cookie/token handling.
- **Later phases**: React Hook Form (as forms grow), Vitest + RTL, Playwright if needed.

---

## 3. Frontend work phases

### Phase 0 — Foundation (required before feature growth)

**Goal**: the project builds; auth and API work.

- [ ] Add **`src/lib/api`**:
  - base URL from env (`NEXT_PUBLIC_API_URL`),
  - shared `fetch`/wrapper with token injection (from cookie or auth context),
  - 401 handling (refresh or redirect to login),
  - **ApiError** class/type with a `body` field for backend details,
  - functions for all used endpoints: studios, slots, bookings, auth (magic link request/verify), payments (as needed).
- [ ] Add **`src/lib/auth`**:
  - **AuthProvider** (context): user, access/refresh (or only a “logged in” flag for cookie-based),
  - **useAuth**: access to user, login/logout, auth checks.
- [ ] Verify frontend **.env.example**: include `NEXT_PUBLIC_API_URL`.
- [ ] Ensure login (magic link) and verify reach a logged-in state and that protected pages (dashboard, bookings) work.

**Outcome**: the app runs; you can log in and navigate studios/bookings/dashboard.

---

### Phase 1 — Stability and validation

**Goal**: predictable forms and types; fewer runtime errors.

- [ ] Introduce **zod** for:
  - API response schemas (where needed — parse after fetch),
  - form schemas (login, booking, create/edit studio).
- [ ] Optionally wire **React Hook Form** + `@hookform/resolvers/zod` for form-heavy pages (login, booking, studio).
- [ ] Unify API error handling on pages (ApiError and backend messages).
- [ ] Add basic unit tests (Vitest + RTL) for critical components and `lib/api`/`lib/auth` (fetch mocks).

**Outcome**: forms validate; errors are handled consistently; foundation for tests.

---

### Phase 2 — UX and polish for public pages

**Goal**: a smooth, fast path: choose studio → slot → book.

- [ ] **Studio list**: filters (city/address, service type), sorting, skeletons, empty states.
- [ ] **Studio card**: photo gallery (if backend returns URLs), clear services and pricing, calendar/date selection for slots.
- [ ] **Booking**: steps (slot → guest details → confirmation), slot availability check before submit, clear messages on conflict/error.
- [ ] **Payment**: after creating booking — redirect to Stripe Checkout; after return from Stripe — success/cancel pages with clear copy and links to “my bookings” / “home”.
- [ ] Responsiveness and accessibility (focus, semantics, aria where needed).

**Outcome**: the public flow from studio list through payment is clear and robust.

---

### Phase 3 — Account and bookings

**Goal**: users and owners see the right information and actions.

- [ ] **My bookings**: list with filters (active/past/cancelled), cancellation with confirmation, pay flow if booking is unpaid.
- [ ] **Booking confirmation** (`/bookings/[id]/confirm`): show details, “Pay” → Stripe, handle already-paid cases.
- [ ] **Owner dashboard**: studio list, create/edit studio, services and schedule management (if API ready), simple metrics (bookings per studio).
- [ ] Notifications/toasts for successful actions (studio created, booking cancelled, etc.) — simple context + Toast component.

**Outcome**: full guest journey and basic owner management.

---

### Phase 4 — Extensions and scale

**Goal**: courses, scheduling, performance.

- [ ] **Courses**: display studio courses, enroll, course payment (use existing payment/order API).
- [ ] **Schedule**: calendar view of slots (calendar library of choice), recurring slots.
- [ ] Optimization: lazy-loaded pages, image optimization (next/image), request caching (TanStack Query already provides basics).
- [ ] If needed — E2E (Playwright) for: guest books and pays; owner creates studio.

**Outcome**: course and schedule support; fast, stable frontend.

---

## 4. Short technology summary

| Category | Choice |
|----------|--------|
| Framework | Next.js 16 (App Router) |
| UI | React 19, TypeScript |
| Styles | Tailwind CSS 4, current design system |
| Data/cache | TanStack Query |
| Auth | Context (AuthProvider) + lib/auth, tokens/cookie |
| API | Unified layer in lib/api with ApiError and refresh |
| Validation | zod (+ optional React Hook Form) |
| Tests | Vitest + React Testing Library; Playwright later |

---

## 5. Next step

Start with **Phase 0**: implement `src/lib/api` and `src/lib/auth`, verify environment variables and the login flow. Then proceed through Phases 1–4 in order.

If useful, a concrete `lib/api` and `lib/auth` implementation can be spelled out for your backend (token format, cookie, refresh endpoint).
