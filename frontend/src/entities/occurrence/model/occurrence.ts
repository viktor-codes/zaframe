import type { OccurrenceResponse } from "./types";

type OccurrenceTiming = Pick<
  OccurrenceResponse,
  "start_time" | "end_time" | "status" | "max_capacity"
>;

export const OCCURRENCE_STATUS = {
  SCHEDULED: "scheduled",
  CANCELLED: "cancelled",
  COMPLETED: "completed",
} as const;

export function isOccurrenceScheduled(
  occurrence: Pick<OccurrenceTiming, "status">,
): boolean {
  return occurrence.status === OCCURRENCE_STATUS.SCHEDULED;
}

export function isOccurrenceCancelled(
  occurrence: Pick<OccurrenceTiming, "status">,
): boolean {
  return occurrence.status === OCCURRENCE_STATUS.CANCELLED;
}

export function isOccurrenceCompleted(
  occurrence: Pick<OccurrenceTiming, "status">,
): boolean {
  return occurrence.status === OCCURRENCE_STATUS.COMPLETED;
}

export function isOccurrenceInPast(
  occurrence: Pick<OccurrenceTiming, "start_time">,
  now: Date = new Date(),
): boolean {
  return new Date(occurrence.start_time).getTime() <= now.getTime();
}

export function isOccurrenceBookable(
  occurrence: Pick<OccurrenceTiming, "start_time" | "status">,
  now: Date = new Date(),
): boolean {
  return isOccurrenceScheduled(occurrence) && !isOccurrenceInPast(occurrence, now);
}

export function getOccurrenceDurationMinutes(
  occurrence: Pick<OccurrenceTiming, "start_time" | "end_time">,
): number {
  const startMs = new Date(occurrence.start_time).getTime();
  const endMs = new Date(occurrence.end_time).getTime();
  const durationMs = Math.max(endMs - startMs, 0);

  return Math.round(durationMs / 60_000);
}

export function getOccurrenceInstructorName(
  occurrence: Pick<OccurrenceResponse, "instructor">,
): string | null {
  return occurrence.instructor?.name ?? null;
}
