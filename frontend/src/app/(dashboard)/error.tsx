"use client";

import { RouteSegmentError } from "@shared/ui";

export default function DashboardError({
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
      title="Dashboard unavailable"
      description="The studio dashboard could not be displayed. Try again or reload the page."
      testId="dashboard-route-error"
    />
  );
}
