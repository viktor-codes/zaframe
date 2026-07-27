"use client";

import { RouteSegmentError } from "@shared/ui";

export default function MainError({
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
      title="This page hit a snag"
      description="The public studio area failed to load. Try again, or head back to studios."
      testId="main-route-error"
    />
  );
}
