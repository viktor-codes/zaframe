import type { ServiceAvailabilityScheduleItem } from "@entities/service";
import { Skeleton } from "@shared/ui";

import {
  formatCourseScheduleDate,
  getScheduleRowCapacityLabel,
} from "../model/course-availability";

export interface CourseSchedulePreviewProps {
  schedule: ServiceAvailabilityScheduleItem[];
  isLoading?: boolean;
  isError?: boolean;
  studioSlug?: string;
  className?: string;
}

/**
 * Read-only list of course dates with remaining/overbooked capacity.
 * No slot selection — course purchase covers the whole term.
 */
export function CourseSchedulePreview({
  schedule,
  isLoading = false,
  isError = false,
  studioSlug,
  className = "",
}: CourseSchedulePreviewProps) {
  if (isLoading) {
    return (
      <div
        className={`space-y-2 ${className}`}
        data-testid="course-schedule-preview-loading"
      >
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-12 w-full rounded-xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className={`rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 ${className}`}
        data-testid="course-schedule-preview-error"
      >
        Could not load course dates. Please try again.
      </div>
    );
  }

  if (schedule.length === 0) {
    return (
      <div
        className={`rounded-2xl border border-dashed border-neutral-200 bg-white px-6 py-10 text-center ${className}`}
        data-testid="course-schedule-preview-empty"
      >
        <p className="font-display text-lg font-semibold text-neutral-900">
          No upcoming sessions
        </p>
        <p className="mt-2 text-sm text-neutral-600">
          Check back later, or browse other classes on the studio page.
        </p>
        {studioSlug ? (
          <a
            href={`/s/${encodeURIComponent(studioSlug)}`}
            className="mt-5 inline-flex text-sm font-semibold text-teal-700 underline"
          >
            Back to studio
          </a>
        ) : null}
      </div>
    );
  }

  return (
    <ul
      className={`divide-y divide-neutral-100 overflow-hidden rounded-2xl border border-neutral-200 bg-white ${className}`}
      data-testid="course-schedule-preview"
    >
      {schedule.map((item) => {
        const capacityLabel = getScheduleRowCapacityLabel(item);
        const isTight = item.is_overbooked || item.remaining <= 0;

        return (
          <li
            key={item.date}
            className="flex items-center justify-between gap-3 px-4 py-3"
            data-overbooked={item.is_overbooked ? "true" : undefined}
          >
            <span className="text-sm font-medium text-neutral-900">
              {formatCourseScheduleDate(item.date)}
            </span>
            <span
              className={`shrink-0 text-xs font-semibold tracking-wide uppercase ${
                isTight ? "text-amber-700" : "text-neutral-500"
              }`}
            >
              {capacityLabel}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
