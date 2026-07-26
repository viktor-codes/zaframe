import { describe, expect, it } from "vitest";

import { isServiceCategory, SERVICE_CATEGORIES } from "./service-category";

describe("SERVICE_CATEGORIES", () => {
  it("includes the OpenAPI yoga category", () => {
    expect(SERVICE_CATEGORIES).toContain("yoga");
  });

  it("narrows known category strings", () => {
    expect(isServiceCategory("pilates")).toBe(true);
    expect(isServiceCategory("unknown")).toBe(false);
  });
});
