"use client";

import { RouteSegmentError } from "@shared/ui";

/**
 * Root App Router error boundary (auth pages and anything outside route groups).
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <RouteSegmentError
      error={error}
      reset={reset}
      title="Something went wrong"
      description="The page could not be loaded. Try again or reload."
      testId="app-root-error"
    />
  );
}
