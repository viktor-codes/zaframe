import type { Page } from "@playwright/test";

export interface GuestBookingDetails {
  name: string;
  email: string;
  phone?: string;
}

export class BookingPage {
  constructor(private readonly page: Page) {}

  async fillGuestDetails(details: GuestBookingDetails): Promise<void> {
    await this.page.getByLabel("Name").fill(details.name);
    await this.page.getByTestId("guest-email-input").fill(details.email);
    if (details.phone) {
      await this.page.getByLabel("Phone (optional)").fill(details.phone);
    }
  }

  async submitBooking(): Promise<void> {
    await this.page.getByTestId("submit-booking-button").click();
  }

  async expectConfirmPage(): Promise<void> {
    await this.page.waitForURL(/\/bookings\/\d+\/confirm/, {
      waitUntil: "domcontentloaded",
    });
    await this.page.getByRole("heading", { name: "Booking details" }).waitFor();
  }
}
