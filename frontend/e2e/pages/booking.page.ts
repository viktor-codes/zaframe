import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

export interface GuestBookingDetails {
  name: string;
  email: string;
  phone?: string;
}

export interface CapturedGuestBooking {
  id: number;
  access_token: string;
  status: string;
}

/**
 * Guest book-occurrence wizard + confirm page helpers.
 * Selectors: data-testid only (see td-10).
 */
export class BookingPage {
  constructor(private readonly page: Page) {}

  async expectWizard(): Promise<void> {
    await expect(this.page.getByTestId("book-occurrence-wizard")).toBeVisible();
  }

  async selectOccurrence(occurrenceId: number): Promise<void> {
    await this.page
      .locator(
        `[data-testid="occurrence-row"][data-occurrence-id="${occurrenceId}"]`,
      )
      .click();
  }

  async continueFromSlot(): Promise<void> {
    await this.page.getByTestId("book-occurrence-button").click();
    await expect(this.page.getByTestId("book-step-details")).toBeVisible();
  }

  async fillGuestDetails(details: GuestBookingDetails): Promise<void> {
    await this.page.getByTestId("guest-name-input").fill(details.name);
    await this.page.getByTestId("guest-email-input").fill(details.email);
    if (details.phone) {
      await this.page.getByTestId("guest-phone-input").fill(details.phone);
    }
  }

  async continueFromDetails(): Promise<void> {
    await this.page.getByTestId("book-details-continue").click();
    await expect(this.page.getByTestId("book-step-summary")).toBeVisible();
  }

  /** Complete wizard steps through summary (does not click Pay). */
  async completeWizardToSummary(
    occurrenceId: number,
    details: GuestBookingDetails,
  ): Promise<void> {
    await this.expectWizard();
    await this.selectOccurrence(occurrenceId);
    await this.continueFromSlot();
    await this.fillGuestDetails(details);
    await this.continueFromDetails();
  }

  /**
   * Intercept POST /bookings so the test gets id + access_token without
   * relying on sessionStorage timing after Pay.
   */
  async armCreateBookingCapture(): Promise<{
    waitForBooking: () => Promise<CapturedGuestBooking>;
  }> {
    const captured: { booking: CapturedGuestBooking | null } = {
      booking: null,
    };

    await this.page.route("**/api/v1/bookings", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const response = await route.fetch();
      const body = (await response.json()) as CapturedGuestBooking & {
        access_token?: string;
      };
      if (
        typeof body.id === "number" &&
        typeof body.access_token === "string" &&
        typeof body.status === "string"
      ) {
        captured.booking = {
          id: body.id,
          access_token: body.access_token,
          status: body.status,
        };
      }
      await route.fulfill({
        status: response.status(),
        headers: response.headers(),
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    });

    return {
      waitForBooking: async () => {
        await expect
          .poll(() => captured.booking, { timeout: 15_000 })
          .not.toBeNull();
        if (captured.booking === null) {
          throw new Error("Guest booking create was not captured.");
        }
        return captured.booking;
      },
    };
  }

  async expectConfirmPage(): Promise<void> {
    await this.page.waitForURL(/\/bookings\/\d+\/confirm/, {
      waitUntil: "domcontentloaded",
    });
    await expect(this.page.getByTestId("guest-confirm-panel")).toBeVisible();
  }

  async readGuestAccessToken(bookingId: number): Promise<string | null> {
    return this.page.evaluate((id) => {
      return sessionStorage.getItem(`zeeframe_booking_access_token_${id}`);
    }, bookingId);
  }
}
