import {
  getOccurrenceRemainingSeats,
  isOccurrenceFull,
  type OccurrenceCapacityCounts,
} from "../model/occurrence";

export interface CapacityIndicatorProps extends OccurrenceCapacityCounts {
  className?: string;
  size?: "sm" | "md";
}

function toneClasses(remaining: number, maxCapacity: number): string {
  if (remaining === 0) {
    return "bg-red-50 text-red-800 border-red-200";
  }

  if (remaining <= Math.max(1, Math.floor(maxCapacity * 0.2))) {
    return "bg-amber-50 text-amber-900 border-amber-200";
  }

  return "bg-emerald-50 text-emerald-900 border-emerald-200";
}

export function CapacityIndicator({
  max_capacity,
  confirmed_count,
  pending_count = 0,
  className = "",
  size = "sm",
}: CapacityIndicatorProps) {
  const capacity = { max_capacity, confirmed_count, pending_count };
  const remaining = getOccurrenceRemainingSeats(capacity);
  const isFull = isOccurrenceFull(capacity);
  const sizeClass =
    size === "md" ? "px-3 py-1.5 text-sm" : "px-2.5 py-1 text-xs";

  let label: string;
  if (isFull) {
    label = "No seats left";
  } else if (remaining === 1) {
    label = "1 seat left";
  } else {
    label = `${remaining} seats left`;
  }

  return (
    <span
      className={`inline-flex items-center rounded-lg border font-semibold ${toneClasses(remaining, max_capacity)} ${sizeClass} ${className}`}
      data-testid="capacity-indicator"
      title={
        pending_count > 0
          ? `${confirmed_count} confirmed · ${pending_count} pending hold`
          : `${confirmed_count} of ${max_capacity} booked`
      }
    >
      {label}
    </span>
  );
}
