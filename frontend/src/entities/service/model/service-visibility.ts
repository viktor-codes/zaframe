import { ServiceVisibility } from "@shared/lib";

export type ServiceVisibilityTone = "neutral" | "amber" | "green" | "teal";

export interface ServiceVisibilityPresentation {
  label: string;
  tone: ServiceVisibilityTone;
  /** Storefront copy for draft/archived badges. */
  storefrontHint: string | null;
}

const PRESENTATION: Record<string, ServiceVisibilityPresentation> = {
  [ServiceVisibility.DRAFT]: {
    label: "Draft",
    tone: "amber",
    storefrontHint: "Not on storefront",
  },
  [ServiceVisibility.PUBLISHED]: {
    label: "Published",
    tone: "green",
    storefrontHint: null,
  },
  [ServiceVisibility.ARCHIVED]: {
    label: "Archived",
    tone: "neutral",
    storefrontHint: "Not on storefront",
  },
};

export function getServiceVisibilityPresentation(
  visibility: string,
): ServiceVisibilityPresentation {
  return (
    PRESENTATION[visibility] ?? {
      label: visibility,
      tone: "teal",
      storefrontHint: null,
    }
  );
}

export function isServiceVisibility(value: string): value is ServiceVisibility {
  return (
    value === ServiceVisibility.DRAFT ||
    value === ServiceVisibility.PUBLISHED ||
    value === ServiceVisibility.ARCHIVED
  );
}
