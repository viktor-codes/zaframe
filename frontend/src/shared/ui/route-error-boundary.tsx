"use client";

/**
 * Client ErrorBoundary wrapper for Server Component route layouts.
 */

import { ErrorBoundary } from "./error-boundary";

export interface RouteErrorBoundaryProps {
  children: React.ReactNode;
  title: string;
  description?: string;
}

export function RouteErrorBoundary({
  children,
  title,
  description,
}: RouteErrorBoundaryProps) {
  return (
    <ErrorBoundary title={title} description={description}>
      {children}
    </ErrorBoundary>
  );
}
