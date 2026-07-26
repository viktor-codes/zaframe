import type { OccurrenceCapacitySummary } from "@entities/occurrence";

export interface TodayCountersProps {
  summary: OccurrenceCapacitySummary;
}

interface CounterItem {
  label: string;
  value: number;
  testId: string;
}

export function TodayCounters({ summary }: TodayCountersProps) {
  const items: CounterItem[] = [
    {
      label: "Sessions",
      value: summary.sessionCount,
      testId: "today-counter-sessions",
    },
    {
      label: "Booked",
      value: summary.confirmedCount,
      testId: "today-counter-booked",
    },
    {
      label: "Pending",
      value: summary.pendingCount,
      testId: "today-counter-pending",
    },
    {
      label: "Capacity",
      value: summary.maxCapacity,
      testId: "today-counter-capacity",
    },
  ];

  return (
    <dl
      className="grid grid-cols-2 gap-3 sm:grid-cols-4"
      data-testid="today-counters"
    >
      {items.map((item) => (
        <div
          key={item.testId}
          className="rounded-xl border border-neutral-200 bg-white px-4 py-3"
          data-testid={item.testId}
        >
          <dt className="text-xs font-semibold tracking-wide text-neutral-500 uppercase">
            {item.label}
          </dt>
          <dd className="mt-1 font-display text-2xl font-bold text-neutral-900">
            {item.value}
          </dd>
        </div>
      ))}
    </dl>
  );
}
