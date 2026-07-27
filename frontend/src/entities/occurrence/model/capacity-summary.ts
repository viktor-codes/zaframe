export interface OccurrenceCapacityInput {
  max_capacity: number;
  confirmed_count?: number | null;
  pending_count?: number | null;
}

export interface OccurrenceCapacitySummary {
  sessionCount: number;
  confirmedCount: number;
  pendingCount: number;
  maxCapacity: number;
  /** confirmed + pending across all sessions. */
  heldSeats: number;
}

/**
 * Aggregate seat counters for a set of sessions (Today overview strip).
 */
export function summarizeOccurrenceCapacity(
  items: readonly OccurrenceCapacityInput[],
): OccurrenceCapacitySummary {
  let confirmedCount = 0;
  let pendingCount = 0;
  let maxCapacity = 0;

  for (const item of items) {
    confirmedCount += Math.max(item.confirmed_count ?? 0, 0);
    pendingCount += Math.max(item.pending_count ?? 0, 0);
    maxCapacity += Math.max(item.max_capacity, 0);
  }

  return {
    sessionCount: items.length,
    confirmedCount,
    pendingCount,
    maxCapacity,
    heldSeats: confirmedCount + pendingCount,
  };
}
