import { Alert } from "@shared/ui";
import type { ServiceAvailabilityResponse } from "@entities/service";

import { getCourseAvailabilityPresentation } from "../model/course-availability";

export interface CourseAvailabilityBannerProps {
  availability: ServiceAvailabilityResponse;
  className?: string;
}

/**
 * Soft/hard capacity warning above the course schedule preview.
 * Renders nothing when availability is clean (`tone === "ok"`).
 */
export function CourseAvailabilityBanner({
  availability,
  className = "",
}: CourseAvailabilityBannerProps) {
  const presentation = getCourseAvailabilityPresentation(availability);

  if (presentation.tone === "ok") {
    return null;
  }

  if (presentation.tone === "blocked") {
    return (
      <Alert
        variant="error"
        title={presentation.title}
        className={className}
        data-testid="course-availability-banner"
        data-tone="blocked"
      >
        {presentation.message}
      </Alert>
    );
  }

  // WHY: shared Alert has no warning variant; amber matches storefront "Limited spots".
  return (
    <div
      role="status"
      className={`rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 ${className}`}
      data-testid="course-availability-banner"
      data-tone="warning"
    >
      <p className="text-sm font-semibold text-amber-950">
        {presentation.title}
      </p>
      <p className="mt-1 text-sm text-amber-900/80">{presentation.message}</p>
    </div>
  );
}
