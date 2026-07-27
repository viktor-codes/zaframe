"use client";

import { RouteSegmentError } from "@shared/ui";

export default function AccountError({
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
      title="Account unavailable"
      description="Your account section could not be displayed. Try again or reload the page."
      testId="account-route-error"
    />
  );
}
