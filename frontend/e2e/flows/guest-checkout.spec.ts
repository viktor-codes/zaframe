/**
 * Guest book → Stripe checkout session (Option A).
 *
 * Mode: hybrid E2E — UI flow through Pay; asserts checkout session created and
 * booking stays pending. Webhook confirmation is covered by backend tests
 * (`backend/tests/test_webhooks.py`).
 *
 * Prerequisites (local):
 *   - PostgreSQL with migrations applied
 *   - Backend `.env`: SECRET_KEY, DATABASE_URL, STRIPE_SECRET_KEY (test mode)
 *   - `make e2e-critical` starts API + Next.js via Playwright webServer
 *
 * Env overrides:
 *   API_URL — backend origin (default http://127.0.0.1:8000)
 *   E2E_STUDIO_ID, E2E_OCCURRENCE_ID, E2E_OCCURRENCE_DATE — skip seed script
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

  test("guest books occurrence and receives Stripe checkout URL", async ({
    page,
  }) => {
    const seed = seedBookableOccurrence();
    const studioPage = new StudioPublicPage(page);
    const bookingPage = new BookingPage(page);
    const stripePage = new StripeCheckoutPage(page);

    await studioPage.goto(seed.studioId);
    await studioPage.setScheduleDate(seed.occurrenceDate);
    await studioPage.clickBookFirstSession();

    await bookingPage.fillGuestDetails(GUEST);
    await bookingPage.submitBooking();
    await bookingPage.expectConfirmPage();

    const urlMatch = page.url().match(/\/bookings\/(\d+)\/confirm/);
    expect(urlMatch).not.toBeNull();
    const bookingId = Number(urlMatch![1]);
    expect(bookingId).toBeGreaterThan(0);

    const guestAccessToken = await page.evaluate((id) => {
      return sessionStorage.getItem(`zeeframe_booking_access_token_${id}`);
    }, bookingId);
    expect(guestAccessToken).toBeTruthy();

    await expect(page.getByTestId("pay-booking-button")).toBeVisible();

    await stripePage.blockStripeRedirect();
    const checkoutBody = await stripePage.clickPayAndCaptureCheckoutSession();

    expect(StripeCheckoutPage.isStripeCheckoutUrl(checkoutBody.checkout_url)).toBe(
      true,
    );
    expect(checkoutBody.session_id).toMatch(/^cs_/);

    if (seed.ownerAccessToken) {
      const booking = await fetchBookingStatusAsOwner(
        API_URL,
        bookingId,
        seed.ownerAccessToken,
      );
      expect(booking.status).toBe("pending");
      expect(booking.payment_status).not.toBe("paid");
    }
  });
});
