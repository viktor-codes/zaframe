export const BOOK_OCCURRENCE_STEPS = ["slot", "details", "summary"] as const;

export type BookOccurrenceStep = (typeof BOOK_OCCURRENCE_STEPS)[number];

export const BOOK_OCCURRENCE_STEP_LABELS: Record<BookOccurrenceStep, string> = {
  slot: "Choose a time",
  details: "Your details",
  summary: "Pay",
};

export function getStepIndex(step: BookOccurrenceStep): number {
  return BOOK_OCCURRENCE_STEPS.indexOf(step);
}
