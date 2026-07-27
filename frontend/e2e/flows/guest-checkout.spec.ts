/**
 * Guest book → Stripe checkout session (Option A / td-10).
 *
 * Flow: `/s/{slug}` → service → wizard (slot → details → summary) → Pay.
 *
 * Mode: hybrid E2E — UI through Pay; asserts Stripe Checkout URL + booking
 * stays `pending`. Webhook → `confirmed` is covered by backend
 * `tests/integration/api/test_webhooks.py`.
 *
 * Option B (local full confirm, not default):
 *   stripe listen --forward-to localhost:8000/webhooks/stripe
 *   then complete Checkout with card 4242… and assert confirmed in UI/API.
 *
 * Prerequisites (local):
 *   - PostgreSQL with migrations applied
 *   - Backend `.env`: SECRET_KEY, DATABASE_URL, STRIPE_SECRET_KEY (test mode)
 *   - `make e2e-critical` starts API + Next.js via Playwright webServer
 *
 * Env overrides (skip seed script):
 *   E2E_STUDIO_ID, E2E_STUDIO_SLUG, E2E_SERVICE_ID,
 *   E2E_OCCURRENCE_ID, E2E_OCCURRENCE_DATE[, E2E_OWNER_ACCESS_TOKEN]
 *   API_URL — backend origin (default http://127.0.0.1:8000)
 *
 * Selectors: data-testid only
 *   service-polaroid-card + data-service-id, book-occurrence-button,
 *   guest-name-input, guest-email-input, submit-booking-button
 */

import { test, expect } from "@playwright/test";

import {
  fetchBookingStatusAsOwner,
  seedBookableOccurrence,
} from "../fixtures/api-seed";
import { BookingPage } from "../pages/booking.page";
import { StripeCheckoutPage } from "../pages/stripe-checkout.page";
import { StudioPublicPage } from "../pages/studio-public.page";

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const GUEST = {
  name: "E2E Guest",
  email: `e2e-guest-${Date.now()}@example.com`,
  phone: "+35310000000",
};

test.describe("guest checkout critical flow", () => {
  test.describe.configure({ mode: "serial" });

  test("guest books via slug storefront and receives Stripe checkout URL", async ({
    page,
  }) => {
    const seed = seedBookableOccurrence();
    const studioPage = new StudioPublicPage(page);
    const bookingPage = new BookingPage(page);
    const stripePage = new StripeCheckoutPage(page);

    await studioPage.gotoBySlug(seed.studioSlug);
    await studioPage.clickServiceById(seed.serviceId);

    await bookingPage.completeWizardToSummary(seed.occurrenceId, GUEST);

    const createCapture = await bookingPage.armCreateBookingCapture();
    await stripePage.blockStripeRedirect();
    const checkoutBody = await stripePage.clickPayAndCaptureCheckoutSession(
      "submit-booking-button",
    );
    const created = await createCapture.waitForBooking();

    expect(
      StripeCheckoutPage.isStripeCheckoutUrl(checkoutBody.checkout_url),
    ).toBe(true);
    expect(checkoutBody.session_id).toMatch(/^cs_/);
    expect(created.id).toBeGreaterThan(0);
    expect(created.access_token.length).toBeGreaterThan(8);
    expect(created.status).toBe("pending");

    const storedToken = await bookingPage.readGuestAccessToken(created.id);
    expect(storedToken).toBe(created.access_token);

    // WHY: GET /bookings/{id} needs a user JWT; guest opaque token is checkout-only.
    // Prefer owner seed token; create-response already proves pending hold.
    if (seed.ownerAccessToken) {
      const ownerView = await fetchBookingStatusAsOwner(
        API_URL,
        created.id,
        seed.ownerAccessToken,
      );
      expect(ownerView.status).toBe("pending");
      expect(ownerView.payment_status).not.toBe("succeeded");
    }
  });
});
