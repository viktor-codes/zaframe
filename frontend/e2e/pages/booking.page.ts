import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

export interface GuestBookingDetails {
  name: string;
  email: string;
  phone?: string;
}

/**
 * Guest book-occurrence wizard + confirm page helpers.
 */
export class BookingPage {
  constructor(private readonly page: Page) {}

  async expectWizard(): Promise<void> {
    await expect(this.page.getByTestId("book-occurrence-wizard")).toBeVisible();
  }

  async selectOccurrence(occurrenceId: number): Promise<void> {
    await this.page
      .locator(`[data-testid="occurrence-row"][data-occurrence-id="${occurrenceId}"]`)
      .click();
  }

  async continueFromSlot(): Promise<void> {
    await this.page.getByTestId("book-slot-continue").click();
    await expect(this.page.getByTestId("book-step-details")).toBeVisible();
  }

  async fillGuestDetails(details: GuestBookingDetails): Promise<void> {
    await this.page.getByLabel("Name").fill(details.name);
    await this.page.getByTestId("guest-email-input").fill(details.email);
    if (details.phone) {
      await this.page.getByLabel("Phone (optional)").fill(details.phone);
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

  async readLatestGuestBookingId(): Promise<number | null> {
    return this.page.evaluate(() => {
      for (let i = 0; i < sessionStorage.length; i += 1) {
        const key = sessionStorage.key(i);
        if (!key?.startsWith("zeeframe_booking_access_token_")) continue;
        const id = Number(key.replace("zeeframe_booking_access_token_", ""));
        if (Number.isInteger(id) && id > 0) return id;
      }
      return null;
    });
  }
}
