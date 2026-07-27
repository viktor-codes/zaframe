"use client";

import type { ServiceAvailabilityResponse } from "@entities/service";

import { getCourseAvailabilityPresentation } from "../model/course-availability";
import { useCourseAvailability } from "../model/use-course-availability";
import { CourseAvailabilityBanner } from "./course-availability-banner";
import { CourseSchedulePreview } from "./course-schedule-preview";

export interface CourseAvailabilityPanelProps {
  serviceId: number;
  studioSlug: string;
  /** Optional YYYY-MM-DD; omit for backend default. */
  startDate?: string | null;
  className?: string;
}

/**
 * Loads public course availability and renders warning + date list.
 */
export function CourseAvailabilityPanel({
  serviceId,
  studioSlug,
  startDate = null,
  className = "",
}: CourseAvailabilityPanelProps) {
  const query = useCourseAvailability({ serviceId, startDate });
  const availability: ServiceAvailabilityResponse | undefined = query.data;

  return (
    <div
      className={`space-y-4 ${className}`}
      data-testid="course-availability-panel"
      data-can-proceed={
        availability
          ? String(getCourseAvailabilityPresentation(availability).canProceed)
          : undefined
      }
    >
      {availability ? (
        <CourseAvailabilityBanner availability={availability} />
      ) : null}

      <div>
        <h2 className="mb-2 font-display text-sm font-semibold tracking-wide text-neutral-500 uppercase">
          Course dates
        </h2>
        <CourseSchedulePreview
          schedule={availability?.schedule_details ?? []}
          isLoading={query.isLoading}
          isError={query.isError}
          studioSlug={studioSlug}
        />
      </div>
    </div>
  );
}
