/**
 * Guest book → Stripe checkout session (Option A) via Phase 3 slug routes.
 *
 * Flow: `/s/{slug}` → service → wizard (slot → details → summary) → Stripe.
 *
 * Mode: hybrid E2E — UI through Pay; asserts checkout session created and
 * booking stays pending. Webhook confirmation is covered by backend tests.
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

    await stripePage.blockStripeRedirect();
    const checkoutBody = await stripePage.clickPayAndCaptureCheckoutSession(
      "submit-booking-button",
    );

    expect(StripeCheckoutPage.isStripeCheckoutUrl(checkoutBody.checkout_url)).toBe(
      true,
    );
    expect(checkoutBody.session_id).toMatch(/^cs_/);

    const bookingId = await bookingPage.readLatestGuestBookingId();
    expect(bookingId).not.toBeNull();
    expect(bookingId!).toBeGreaterThan(0);

    const guestAccessToken = await bookingPage.readGuestAccessToken(bookingId!);
    expect(guestAccessToken).toBeTruthy();

    if (seed.ownerAccessToken) {
      const booking = await fetchBookingStatusAsOwner(
        API_URL,
        bookingId!,
        seed.ownerAccessToken,
      );
      expect(booking.status).toBe("pending");
      expect(booking.payment_status).not.toBe("succeeded");
    }
  });
});
