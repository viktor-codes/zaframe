/**
 * Pure presentation helpers for course availability (purchase warnings).
 * STRATEGY §7: warn before purchase when dates are overbooked.
 */

import type {
  ServiceAvailabilityResponse,
  ServiceAvailabilityScheduleItem,
} from "@entities/service";

export type CourseAvailabilityTone = "ok" | "warning" | "blocked";

export interface CourseAvailabilityPresentation {
  tone: CourseAvailabilityTone;
  /** Whether checkout CTA may proceed. */
  canProceed: boolean;
  title: string;
  message: string;
  overbookedCount: number;
}

export const COURSE_NO_SESSIONS_TITLE = "No upcoming sessions";
export const COURSE_NO_SESSIONS_MESSAGE =
  "This course has no bookable dates yet. Check back later or browse other classes.";

export const COURSE_HARD_BLOCK_TITLE = "Course is full on key dates";
export const COURSE_HARD_BLOCK_MESSAGE =
  "Not enough seats across several sessions. Contact the studio or pick another class.";

export const COURSE_SOFT_WARNING_TITLE = "Some dates are almost full";
export const COURSE_SOFT_WARNING_MESSAGE =
  "You can still buy the course — a few sessions may have limited spots left.";

const HARD_LIMIT = "HARD_LIMIT_REACHED";

/**
 * Map API availability into UI tone + JTBD copy.
 * Prefers API `warning_message` when present; falls back to stable frontend copy.
 */
export function getCourseAvailabilityPresentation(
  availability: ServiceAvailabilityResponse,
): CourseAvailabilityPresentation {
  const overbookedCount = availability.schedule_details.filter(
    (item) => item.is_overbooked,
  ).length;

  if (!availability.can_book) {
    const isEmpty = availability.schedule_details.length === 0;
    return {
      tone: "blocked",
      canProceed: false,
      title: isEmpty ? COURSE_NO_SESSIONS_TITLE : COURSE_HARD_BLOCK_TITLE,
      message:
        availability.warning_message?.trim() ||
        (isEmpty ? COURSE_NO_SESSIONS_MESSAGE : COURSE_HARD_BLOCK_MESSAGE),
      overbookedCount,
    };
  }

  if (availability.requires_warning) {
    return {
      tone: "warning",
      canProceed: true,
      title: COURSE_SOFT_WARNING_TITLE,
      message:
        availability.warning_message?.trim() || COURSE_SOFT_WARNING_MESSAGE,
      overbookedCount,
    };
  }

  return {
    tone: "ok",
    canProceed: true,
    title: "",
    message: "",
    overbookedCount: 0,
  };
}

export function formatCourseScheduleDate(
  isoDate: string,
  locale = "en-IE",
): string {
  // WHY: API returns YYYY-MM-DD; parse as local noon to avoid TZ day-shift.
  const date = new Date(`${isoDate}T12:00:00`);
  if (Number.isNaN(date.getTime())) {
    return isoDate;
  }
  return date.toLocaleDateString(locale, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

export function getScheduleRowCapacityLabel(
  item: ServiceAvailabilityScheduleItem,
): string {
  if (item.overbooking_status === HARD_LIMIT || item.remaining <= 0) {
    return "Full";
  }
  if (item.is_overbooked) {
    return "Limited";
  }
  if (item.remaining === 1) {
    return "1 seat left";
  }
  return `${item.remaining} seats left`;
}
