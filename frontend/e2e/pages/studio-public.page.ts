import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Public storefront `/s/[slug]` (Phase 3 slug routes).
 */
export class StudioPublicPage {
  constructor(private readonly page: Page) {}

  async gotoBySlug(slug: string): Promise<void> {
    await this.page.goto(`/s/${encodeURIComponent(slug)}`);
    await expect(this.page.getByTestId("studio-storefront")).toBeVisible();
  }

  async clickFirstService(): Promise<void> {
    await this.page.getByTestId("service-polaroid-card").first().click();
    await this.page.waitForURL(/\/s\/[^/]+\/book\/\d+/, {
      waitUntil: "domcontentloaded",
    });
  }

  async clickServiceById(serviceId: number): Promise<void> {
    await this.page
      .locator(
        `[data-testid="service-polaroid-card"][data-service-id="${serviceId}"]`,
      )
      .click();
    await this.page.waitForURL(new RegExp(`/book/${serviceId}$`), {
      waitUntil: "domcontentloaded",
    });
  }
}
