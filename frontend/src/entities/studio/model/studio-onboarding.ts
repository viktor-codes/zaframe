import { roleHasPermission, ServiceVisibility, StudioPermission } from "@shared/lib";

import { hasStudioSlug } from "./studio";
import type { StudioWithRoleResponse } from "./types";

export type StudioOnboardingStepId =
  | "complete_profile"
  | "connect_stripe"
  | "create_service"
  | "publish_service"
  | "ready";

export interface StudioOnboardingStep {
  id: StudioOnboardingStepId;
  title: string;
  description: string;
  href: string;
  ctaLabel: string;
}

type StudioOnboardingInput = Pick<
  StudioWithRoleResponse,
  "id" | "slug" | "city" | "description" | "role"
>;

type ServiceVisibilityInput = {
  visibility: string;
};

/** Connect flags for funnel gating — `undefined` while status is still loading. */
export type StudioConnectOnboardingInput =
  | {
      stripe_account_id?: string | null;
      stripe_charges_enabled: boolean;
      stripe_payouts_enabled: boolean;
    }
  | undefined;

function isProfileIncomplete(studio: StudioOnboardingInput): boolean {
  const city = studio.city?.trim() ?? "";
  const description = studio.description?.trim() ?? "";
  return !hasStudioSlug(studio) || city.length === 0 || description.length === 0;
}

function isConnectIncomplete(connect: NonNullable<StudioConnectOnboardingInput>): boolean {
  const accountId = connect.stripe_account_id?.trim() ?? "";
  if (!accountId) return true;
  return !(connect.stripe_charges_enabled && connect.stripe_payouts_enabled);
}

/**
 * Next onboarding action for a membership studio.
 *
 * Funnel (STRATEGY): profile → Stripe Connect → create/publish service.
 *
 * @param services - `undefined` when the caller cannot/should not load services yet.
 * @param connect - `undefined` while Connect status is loading for a payouts manager.
 */
export function resolveStudioOnboardingStep(
  studio: StudioOnboardingInput,
  services: ReadonlyArray<ServiceVisibilityInput> | undefined,
  connect: StudioConnectOnboardingInput = undefined,
): StudioOnboardingStep | null {
  const base = `/dashboard/studios/${studio.id}`;

  const canManageStudio = roleHasPermission(
    studio.role,
    StudioPermission.MANAGE_STUDIO,
  );

  // WHY: only owners can edit profile — never send manager/instructor to /profile.
  if (isProfileIncomplete(studio) && canManageStudio) {
    return {
      id: "complete_profile",
      title: "Complete studio profile",
      description:
        "Add a public slug, city, and short description so customers can find you.",
      href: `${base}/profile`,
      ctaLabel: "Edit profile",
    };
  }

  const canManagePayouts = roleHasPermission(
    studio.role,
    StudioPermission.MANAGE_PAYOUTS,
  );

  if (canManagePayouts) {
    // Connect status still loading — wait before guessing.
    if (connect === undefined) {
      return null;
    }
    if (isConnectIncomplete(connect)) {
      return {
        id: "connect_stripe",
        title: "Connect Stripe to get paid",
        description:
          "Finish Stripe Connect so customers can pay for classes and you can receive payouts.",
        href: `${base}/payouts`,
        ctaLabel: "Set up payouts",
      };
    }
  }

  const canManageServices = roleHasPermission(
    studio.role,
    StudioPermission.MANAGE_SERVICES,
  );

  if (!canManageServices) {
    return {
      id: "ready",
      title: "Studio ready",
      description: "Open Today to see sessions and check participants in.",
      href: base,
      ctaLabel: "Open Today",
    };
  }

  // Services still loading for an owner/manager — wait before guessing.
  if (services === undefined) {
    return null;
  }

  if (services.length === 0) {
    return {
      id: "create_service",
      title: "Create your first service",
      description:
        "Add a class or course as a draft, then publish it to the storefront.",
      href: `${base}/services`,
      ctaLabel: "Add service",
    };
  }

  const hasPublished = services.some(
    (service) => service.visibility === ServiceVisibility.PUBLISHED,
  );

  if (!hasPublished) {
    return {
      id: "publish_service",
      title: "Publish a service",
      description:
        "Drafts stay private. Publish one service so customers can book.",
      href: `${base}/services`,
      ctaLabel: "Review services",
    };
  }

  return {
    id: "ready",
    title: "Studio ready",
    description: "Open Today to run the day, or keep refining schedule and bookings.",
    href: base,
    ctaLabel: "Open Today",
  };
}

/**
 * First incomplete studio wins; if all ready, spotlight the first membership.
 */
export function pickSpotlightStudioStep(
  studios: ReadonlyArray<StudioOnboardingInput>,
  servicesByStudioId: ReadonlyMap<
    number,
    ReadonlyArray<ServiceVisibilityInput> | undefined
  >,
  connectByStudioId: ReadonlyMap<number, StudioConnectOnboardingInput> = new Map(),
): { studio: StudioOnboardingInput; step: StudioOnboardingStep } | null {
  if (studios.length === 0) {
    return null;
  }

  for (const studio of studios) {
    const step = resolveStudioOnboardingStep(
      studio,
      servicesByStudioId.get(studio.id),
      connectByStudioId.get(studio.id),
    );
    if (step == null) {
      continue;
    }
    if (step.id !== "ready") {
      return { studio, step };
    }
  }

  const first = studios[0];
  const step = resolveStudioOnboardingStep(
    first,
    servicesByStudioId.get(first.id),
    connectByStudioId.get(first.id),
  );
  if (step == null) {
    return null;
  }
  return { studio: first, step };
}
