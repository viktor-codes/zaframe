import type { OccurrenceDateGroup } from "@entities/occurrence";

import { CalendarOccurrenceCard } from "./calendar-occurrence-card";

export interface CalendarDayGroupProps {
  studioId: number;
  group: OccurrenceDateGroup;
}

export function CalendarDayGroup({ studioId, group }: CalendarDayGroupProps) {
  return (
    <section
      className="space-y-3"
      aria-labelledby={`calendar-day-${group.dateKey}`}
      data-testid={`calendar-day-${group.dateKey}`}
    >
      <h2
        id={`calendar-day-${group.dateKey}`}
        className="text-sm font-semibold tracking-wide text-neutral-500 uppercase"
      >
        {group.label}
      </h2>
      <div className="grid gap-3">
        {group.occurrences.map((occurrence) => (
          <CalendarOccurrenceCard
            key={occurrence.id}
            studioId={studioId}
            occurrence={occurrence}
          />
        ))}
      </div>
    </section>
  );
}
