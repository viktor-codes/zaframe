/**
 * Schedule template weekdays — matches API contract (0=Monday .. 6=Sunday).
 */

export const DAY_OF_WEEK = {
  MONDAY: 0,
  TUESDAY: 1,
  WEDNESDAY: 2,
  THURSDAY: 3,
  FRIDAY: 4,
  SATURDAY: 5,
  SUNDAY: 6,
} as const;

export type DayOfWeek = (typeof DAY_OF_WEEK)[keyof typeof DAY_OF_WEEK];

export interface DayOfWeekOption {
  value: DayOfWeek;
  label: string;
  shortLabel: string;
}

export const DAY_OF_WEEK_OPTIONS: readonly DayOfWeekOption[] = [
  { value: DAY_OF_WEEK.MONDAY, label: "Monday", shortLabel: "Mon" },
  { value: DAY_OF_WEEK.TUESDAY, label: "Tuesday", shortLabel: "Tue" },
  { value: DAY_OF_WEEK.WEDNESDAY, label: "Wednesday", shortLabel: "Wed" },
  { value: DAY_OF_WEEK.THURSDAY, label: "Thursday", shortLabel: "Thu" },
  { value: DAY_OF_WEEK.FRIDAY, label: "Friday", shortLabel: "Fri" },
  { value: DAY_OF_WEEK.SATURDAY, label: "Saturday", shortLabel: "Sat" },
  { value: DAY_OF_WEEK.SUNDAY, label: "Sunday", shortLabel: "Sun" },
] as const;

const BY_VALUE = new Map<number, DayOfWeekOption>(
  DAY_OF_WEEK_OPTIONS.map((option) => [option.value, option]),
);

export function isDayOfWeek(value: number): value is DayOfWeek {
  return BY_VALUE.has(value);
}

export function getDayOfWeekLabel(dayOfWeek: number): string {
  return BY_VALUE.get(dayOfWeek)?.label ?? `Day ${dayOfWeek}`;
}

export function getDayOfWeekShortLabel(dayOfWeek: number): string {
  return BY_VALUE.get(dayOfWeek)?.shortLabel ?? `D${dayOfWeek}`;
}
