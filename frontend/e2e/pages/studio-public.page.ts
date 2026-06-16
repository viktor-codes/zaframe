import type { Page } from "@playwright/test";

export class StudioPublicPage {
  constructor(private readonly page: Page) {}

  async goto(studioId: number): Promise<void> {
    await this.page.goto(`/studios/${studioId}`);
  }

  async setScheduleDate(isoDate: string): Promise<void> {
    await this.page.locator('input[type="date"]').fill(isoDate);
  }

  async clickBookFirstSession(): Promise<void> {
    await this.page.getByTestId("book-occurrence-button").first().click();
  }
}
