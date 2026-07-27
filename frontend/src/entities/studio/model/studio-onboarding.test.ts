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

const connectReady = {
  stripe_account_id: "acct_ready",
  stripe_charges_enabled: true,
  stripe_payouts_enabled: true,
};

const connectIncomplete = {
  stripe_account_id: null as string | null,
  stripe_charges_enabled: false,
  stripe_payouts_enabled: false,
};

describe("resolveStudioOnboardingStep", () => {
  it("asks for profile when slug, city, or description is missing", () => {
    const step = resolveStudioOnboardingStep(
      { ...baseStudio, slug: null },
      [],
      connectIncomplete,
    );
    expect(step?.id).toBe("complete_profile");
    expect(step?.href).toBe("/dashboard/studios/7/profile");
  });

  it("skips incomplete profile for managers who cannot edit it", () => {
    const step = resolveStudioOnboardingStep(
      {
        ...baseStudio,
        role: StudioMemberRole.MANAGER,
        slug: null,
      },
      [],
      connectReady,
    );
    expect(step?.id).toBe("create_service");
  });

  it("asks managers to connect Stripe before creating a service", () => {
    const step = resolveStudioOnboardingStep(
      {
        ...baseStudio,
        role: StudioMemberRole.MANAGER,
        slug: null,
      },
      [],
      connectIncomplete,
    );
    expect(step?.id).toBe("connect_stripe");
    expect(step?.href).toBe("/dashboard/studios/7/payouts");
  });

  it("skips incomplete profile for instructors and marks ready", () => {
    const step = resolveStudioOnboardingStep(
      {
        ...baseStudio,
        role: StudioMemberRole.INSTRUCTOR,
        slug: null,
      },
      undefined,
    );
    expect(step?.id).toBe("ready");
  });

  it("skips service steps for instructors and marks ready", () => {
    const step = resolveStudioOnboardingStep(
      { ...baseStudio, role: StudioMemberRole.INSTRUCTOR },
      undefined,
    );
    expect(step?.id).toBe("ready");
  });

  it("returns null while Connect status is still loading for owners", () => {
    expect(resolveStudioOnboardingStep(baseStudio, [], undefined)).toBeNull();
  });

  it("asks to connect Stripe when Connect is incomplete", () => {
    const step = resolveStudioOnboardingStep(
      baseStudio,
      [],
      connectIncomplete,
    );
    expect(step?.id).toBe("connect_stripe");
  });

  it("returns null while owner services are still loading after Connect", () => {
    expect(
      resolveStudioOnboardingStep(baseStudio, undefined, connectReady),
    ).toBeNull();
  });

  it("asks to create a service when the catalog is empty", () => {
    expect(
      resolveStudioOnboardingStep(baseStudio, [], connectReady)?.id,
    ).toBe("create_service");
  });

  it("asks to publish when only drafts exist", () => {
    const step = resolveStudioOnboardingStep(
      baseStudio,
      [{ visibility: ServiceVisibility.DRAFT }],
      connectReady,
    );
    expect(step?.id).toBe("publish_service");
  });

  it("marks ready when at least one service is published", () => {
    const step = resolveStudioOnboardingStep(
      baseStudio,
      [
        { visibility: ServiceVisibility.DRAFT },
        { visibility: ServiceVisibility.PUBLISHED },
      ],
      connectReady,
    );
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
    const connect = new Map([
      [1, connectReady],
      [2, connectReady],
    ]);
    const spotlight = pickSpotlightStudioStep(studios, services, connect);
    expect(spotlight?.studio.id).toBe(2);
    expect(spotlight?.step.id).toBe("complete_profile");
  });
});
