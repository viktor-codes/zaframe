import { describe, expect, it } from "vitest";

import { ServiceVisibility, StudioMemberRole } from "@shared/lib";

import {
  pickSpotlightStudioStep,
  resolveStudioOnboardingStep,
} from "./studio-onboarding";

const baseStudio = {
  id: 7,
  slug: "yoga-hub",
  city: "Dublin",
  description: "Bright studio",
  role: StudioMemberRole.OWNER,
};

describe("resolveStudioOnboardingStep", () => {
  it("asks for profile when slug, city, or description is missing", () => {
    const step = resolveStudioOnboardingStep(
      { ...baseStudio, slug: null },
      [],
    );
    expect(step?.id).toBe("complete_profile");
    expect(step?.href).toBe("/dashboard/studios/7/profile");
  });

  it("skips service steps for instructors and marks ready", () => {
    const step = resolveStudioOnboardingStep(
      { ...baseStudio, role: StudioMemberRole.INSTRUCTOR },
      undefined,
    );
    expect(step?.id).toBe("ready");
  });

  it("returns null while owner services are still loading", () => {
    expect(resolveStudioOnboardingStep(baseStudio, undefined)).toBeNull();
  });

  it("asks to create a service when the catalog is empty", () => {
    expect(resolveStudioOnboardingStep(baseStudio, [])?.id).toBe(
      "create_service",
    );
  });

  it("asks to publish when only drafts exist", () => {
    const step = resolveStudioOnboardingStep(baseStudio, [
      { visibility: ServiceVisibility.DRAFT },
    ]);
    expect(step?.id).toBe("publish_service");
  });

  it("marks ready when at least one service is published", () => {
    const step = resolveStudioOnboardingStep(baseStudio, [
      { visibility: ServiceVisibility.DRAFT },
      { visibility: ServiceVisibility.PUBLISHED },
    ]);
    expect(step?.id).toBe("ready");
  });
});

describe("pickSpotlightStudioStep", () => {
  it("prefers the first studio that is not ready", () => {
    const studios = [
      { ...baseStudio, id: 1 },
      { ...baseStudio, id: 2, slug: null },
    ];
    const services = new Map<number, { visibility: string }[] | undefined>([
      [1, [{ visibility: ServiceVisibility.PUBLISHED }]],
      [2, []],
    ]);
    const spotlight = pickSpotlightStudioStep(studios, services);
    expect(spotlight?.studio.id).toBe(2);
    expect(spotlight?.step.id).toBe("complete_profile");
  });
});
