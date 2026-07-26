import Link from "next/link";

import {
  BOOK_OCCURRENCE_STEP_LABELS,
  getStepIndex,
  type BookOccurrenceStep,
} from "../model/steps";

export interface WizardChromeProps {
  slug: string;
  studioName: string;
  serviceName: string;
  step: BookOccurrenceStep;
  children: React.ReactNode;
}

export function WizardChrome({
  slug,
  studioName,
  serviceName,
  step,
  children,
}: WizardChromeProps) {
  const stepIndex = getStepIndex(step);

  return (
    <div
      className="mx-auto max-w-xl px-4 pt-28 pb-16 sm:px-6"
      data-testid="book-occurrence-wizard"
    >
      <Link
        href={`/s/${encodeURIComponent(slug)}`}
        className="mb-6 inline-block text-sm font-medium text-teal-700 hover:text-teal-800"
      >
        ← Back to {studioName}
      </Link>

      <h1 className="font-display text-2xl font-bold text-neutral-900">
        Book {serviceName}
      </h1>
      <p className="mt-1 text-sm text-neutral-600">{studioName}</p>

      <ol className="mt-6 mb-8 flex flex-wrap gap-2 text-xs font-semibold tracking-wide uppercase">
        {(["slot", "details", "summary"] as const).map((item, index) => (
          <li
            key={item}
            className={`rounded-full px-3 py-1 ${
              index === stepIndex
                ? "bg-neutral-900 text-white"
                : index < stepIndex
                  ? "bg-teal-100 text-teal-800"
                  : "bg-neutral-100 text-neutral-500"
            }`}
          >
            {index + 1}. {BOOK_OCCURRENCE_STEP_LABELS[item]}
          </li>
        ))}
      </ol>

      {children}
    </div>
  );
}
