import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

export interface CheckoutSessionPayload {
  checkout_url: string;
  session_id: string;
}

/**
 * Stripe hosted checkout helpers.
 *
 * E2E mode A (default): assert checkout session API response only — do not
 * complete payment or simulate webhooks (see test_webhooks.py for that).
 */
export class StripeCheckoutPage {
  constructor(private readonly page: Page) {}

  /**
   * Block navigation to Stripe so the test stays on-app (Option A).
   */
  async blockStripeRedirect(): Promise<void> {
    await this.page.route("**/*", async (route) => {
      const url = route.request().url();
      if (url.includes("checkout.stripe.com")) {
        await route.abort();
        return;
      }
      await route.continue();
    });
  }

  /**
   * Click Pay and capture checkout session JSON before Stripe redirect runs.
   * @param payTestId - wizard summary uses `submit-booking-button`;
   *   confirm page uses `pay-booking-button`.
   */
  async clickPayAndCaptureCheckoutSession(
    payTestId: "submit-booking-button" | "pay-booking-button" = "submit-booking-button",
  ): Promise<CheckoutSessionPayload> {
    const captured: { payload: CheckoutSessionPayload | null } = {
      payload: null,
    };

    await this.page.route("**/api/v1/payments/checkout-session", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const response = await route.fetch();
      const body = (await response.json()) as CheckoutSessionPayload;
      captured.payload = body;
      await route.fulfill({
        status: response.status(),
        headers: response.headers(),
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    });

    await this.page.getByTestId(payTestId).click();

    await expect
      .poll(() => captured.payload, { timeout: 15_000 })
      .not.toBeNull();

    if (captured.payload === null) {
      throw new Error(
        "Checkout session payload was not captured before timeout.",
      );
    }

    return captured.payload;
  }

  static isStripeCheckoutUrl(url: string): boolean {
    return url.includes("checkout.stripe.com");
  }
}
