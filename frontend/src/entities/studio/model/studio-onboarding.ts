import { roleHasPermission, ServiceVisibility, StudioPermission } from "@shared/lib";

import { hasStudioSlug } from "./studio";
import type { StudioWithRoleResponse } from "./types";

export type StudioOnboardingStepId =
  | "complete_profile"
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

function isProfileIncomplete(studio: StudioOnboardingInput): boolean {
  const city = studio.city?.trim() ?? "";
  const description = studio.description?.trim() ?? "";
  return !hasStudioSlug(studio) || city.length === 0 || description.length === 0;
}

/**
 * Next onboarding action for a membership studio.
 *
 * WHY: Stripe Connect is Phase 6 — skipped here. Schedule/occurrence depth
 * waits for manage-schedule; after a published service we treat the studio as ready.
 *
 * @param services - `undefined` when the caller cannot/should not load services yet.
 */
export function resolveStudioOnboardingStep(
  studio: StudioOnboardingInput,
  services: ReadonlyArray<ServiceVisibilityInput> | undefined,
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
): { studio: StudioOnboardingInput; step: StudioOnboardingStep } | null {
  if (studios.length === 0) {
    return null;
  }

  for (const studio of studios) {
    const step = resolveStudioOnboardingStep(
      studio,
      servicesByStudioId.get(studio.id),
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
  );
  if (step == null) {
    return null;
  }
  return { studio: first, step };
}
