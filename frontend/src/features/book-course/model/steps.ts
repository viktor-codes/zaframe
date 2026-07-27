export const BOOK_COURSE_STEPS = ["preview", "details", "summary"] as const;

export type BookCourseStep = (typeof BOOK_COURSE_STEPS)[number];

export const BOOK_COURSE_STEP_LABELS: Record<BookCourseStep, string> = {
  preview: "Course dates",
  details: "Your details",
  summary: "Pay",
};

export function getBookCourseStepIndex(step: BookCourseStep): number {
  return BOOK_COURSE_STEPS.indexOf(step);
}
