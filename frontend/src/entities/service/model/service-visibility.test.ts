import { describe, expect, it } from "vitest";

import { ServiceVisibility } from "@shared/lib";

import { getServiceVisibilityPresentation } from "./service-visibility";

describe("getServiceVisibilityPresentation", () => {
  it("marks drafts as not on the storefront", () => {
    const presentation = getServiceVisibilityPresentation(
      ServiceVisibility.DRAFT,
    );
    expect(presentation.label).toBe("Draft");
    expect(presentation.storefrontHint).toBe("Not on storefront");
  });

  it("clears the storefront hint for published services", () => {
    expect(
      getServiceVisibilityPresentation(ServiceVisibility.PUBLISHED)
        .storefrontHint,
    ).toBeNull();
  });
});
