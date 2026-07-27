# ZeeFrame Frontend — STRATEGY

> What we build and why. Living document — update it when a decision changes.
> Companion docs: [ARCHITECTURE.md](./ARCHITECTURE.md), [CONTRACTS.md](./CONTRACTS.md), [ROADMAP.md](./ROADMAP.md).

## 1. Product (one sentence)

**ZeeFrame** is a marketplace/storefront for photo and video studios: a customer finds a class
and books it with payment; a studio owner and their team publish services, generate a schedule,
and manage bookings.

Backend domain (already implemented):

```text
Studio → Service (single | course) → Occurrence → Booking → Order → Payment
```

## 2. Three surfaces and personas

| Surface | Who | Job to be done |
|---------|-----|----------------|
| **Storefront** (public) | Guest / customer | "Find a class and book it" |
| **Account** | Authenticated customer | "My bookings, payments, cancellations" |
| **Dashboard** | Owner / Manager / Instructor | "Sell and run the day" |

Key IA fact: one person can be both a customer and staff of several studios.
The header must switch modes explicitly ("Customer ↔ Studio {name}") — never mix
"my bookings" with "studio bookings" in one navigation.

The word **"dashboard" is reserved for the studio surface**. The customer surface is "account".

## 3. Decisions — RESOLVED (2026-07-05)

| # | Question | Decision |
|---|----------|----------|
| 1 | UI language | **EN only** for MVP. i18n later if needed. |
| 2 | Storefront routing | **`/s/{slug}`** from Phase 3 (backend already serves `GET /studios/slug/{slug}/public`). `/studios/[id]` public page is retired. |
| 3 | Homepage | Keep the **marketing landing** (do not touch) + add a search block. Catalog lives at `/studios`. |
| 4 | Account URL | **`/account/*`** (bookings, orders, profile). Current `/bookings/*` pages migrate there. |
| 5 | Dashboard schedule view | **List grouped by date** for MVP. Week calendar → P2. |
| 6 | Mobile priority | Storefront + check-in are **mobile-first**; dashboard is **desktop-first** (must not break on mobile). |
| 7 | Pagination contract | Backend adds the **`{items, total, page, size}` envelope** to list endpoints **before** frontend list screens are built (see CONTRACTS §5, backlog for backend). |
| 8 | Machine-readable error codes | **Deferred.** MVP distinguishes errors by HTTP status + `detail` text. `code` field → backlog. |
| 9 | Docs location | `frontend/docs/` (this folder). |

## 4. Core UX principles (locked)

- **Guest-first checkout.** Booking without an account via `access_token`. Offer sign-in
  **after** successful payment, never before — it kills conversion.
- **Storefront only sees `published`.** Draft/archived services never leak to the public surface.
- **Two schedule modes, physically separated in the UI:**
  1. **Templates** (recurring rules) → `POST /studios/{id}/generate-occurrences`
  2. **Calendar** (concrete occurrences) → edit / cancel with reason
  Template edits never mutate existing occurrences. The UI must state this explicitly:
  *"Template changes affect future generations only. Edit existing sessions in the calendar."*
- **Owner onboarding funnel is the dashboard's spine.** The dashboard leads the owner through
  it instead of showing empty sections:

```text
Sign in → Create studio → Profile/slug → Stripe Connect
→ Create service (draft) → Publish → Schedule template → Generate
→ Check storefront → Wait for first booking
```

- **Single vs Course are different flows.** Different card layouts, different booking wizards.
  Course = one purchase (Order) covering a term of occurrences.

## 5. User stories

### P0 — product does not live without these (spec fully, build first)

1. **Guest** finds a studio → picks a single class → pays → sees success page.
2. **Customer** signs in via OTP and sees the booking in "My bookings" (guest bookings merge by email).
3. **Owner** creates a studio → service → generates occurrences → sees them on the storefront.
4. **Owner** sees a new booking in the dashboard.
5. **Customer** cancels a booking before the cutoff (`cancel_before_hours`).

### P1 — right after MVP (titles only, detail when picked up)

6. Course booking (order + multiple occurrences).
7. Stripe Connect onboarding inside the dashboard.
8. Check-in / no-show (instructor flow).
9. Team members (invite manager/instructor).

### P2 — polish (backlog list)

10. Search/filters on `/studios`.
11. Week-view calendar in the dashboard.

**Done (Wave 1):** GDPR export / delete account (`GET /me/export`, delete UI, privacy/cookies).

## 6. URL tree (agreed)

```text
# Public
/                               → marketing landing + search block (do not redesign)
/studios                        → studio catalog / search
/s/{slug}                       → studio storefront (public API)
/s/{slug}/book/{serviceId}      → booking wizard (single or course)
/bookings/success               → post-payment confirmation
/bookings/{id}/confirm          → guest booking view (#access_token= preferred)

# Auth
/auth/login                     → OTP request
/auth/verify                    → OTP verify

# Account (customer)
/account/bookings               → upcoming / past / cancelled
/account/orders                 → course orders
/account/profile                → name, phone, marketing consent

# Dashboard (studio staff)
/dashboard                      → my studios list (GET /studios/my)
/dashboard/studios/new          → create studio
/dashboard/studios/{id}         → "Today" overview: sessions, counters, quick actions
/dashboard/studios/{id}/profile → name, slug, logo, timezone, cancel policy
/dashboard/studios/{id}/services            → CRUD + draft/published/archived
/dashboard/studios/{id}/services/{sid}/schedule → templates + generate
/dashboard/studios/{id}/calendar            → occurrences list by date (edit/cancel)
/dashboard/studios/{id}/bookings            → studio bookings
/dashboard/studios/{id}/occurrences/{oid}   → participants + check-in
/dashboard/studios/{id}/team                → members (P1)
/dashboard/studios/{id}/payouts             → Stripe Connect status (P1)
```

Access per zone: public → everyone; `/account` → authenticated user;
`/dashboard` → user with at least one studio role; sections gated by studio permissions
(see CONTRACTS §2). Instructor sees a reduced dashboard: today's sessions, participants,
check-in — no services/schedule/payouts.

## 7. Edge cases — must be designed, not discovered

| Situation | UI behaviour |
|-----------|--------------|
| Occurrence full | Disabled CTA + "No seats left" |
| Pending booking (unpaid) | Hold timer + "Complete payment" action |
| Stripe webhook delayed | "Payment processing…" + polling on success page |
| Occurrence cancelled by studio | Account: "Session cancelled by the studio" + reason |
| Course has overbooked dates | Warning from `PublicService.availability` before purchase |
| Draft service | Dashboard only, badge "Not on storefront" |
| Instructor w/o `manage_schedule` | Schedule menu item absent (PermissionGate) |
| Booking expired (`expired` status) | Account: "Payment window expired" + rebook CTA |

## 8. Definition of Done — every screen

- [ ] Loading state
- [ ] Error state (Problem JSON parsed, friendly message)
- [ ] Empty state with JTBD copy + CTA (not "no data")
- [ ] Mobile verified (storefront/check-in: mobile-first)
- [ ] Relevant edge cases from §7 covered
- [ ] Types generated from OpenAPI — no hand-written API types
