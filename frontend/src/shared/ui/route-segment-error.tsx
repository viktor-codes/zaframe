"use client";

/**
 * Fallback UI for Next.js `error.tsx` route segment files.
 *
 * WHY: class ErrorBoundary in layouts does not catch RSC/SSR segment failures;
 * App Router `error.tsx` does. Keep copy/UX aligned with ResourceErrorState.
 */

import { useEffect } from "react";

import { ResourceErrorState } from "./resource-states";

export interface RouteSegmentErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
  title: string;
  description: string;
  testId: string;
}

export function RouteSegmentError({
  error,
  reset,
  title,
  description,
  testId,
}: RouteSegmentErrorProps) {
  useEffect(() => {
    // WHY: digest correlates with server logs; message may be generic in prod.
    console.error("[RouteSegmentError]", error.digest ?? error.message);
  }, [error]);

  return (
    <div className="mx-auto flex min-h-[40vh] max-w-lg items-center p-6">
      <ResourceErrorState
        title={title}
        message={description}
        testId={testId}
        onRetry={reset}
      />
    </div>
  );
}
