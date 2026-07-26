"use client";

/**
 * Client ErrorBoundary wrapper for Server Component route layouts.
 * Remounts on pathname change so a failed page does not block the next route.
 */

import { usePathname } from "next/navigation";

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
  const pathname = usePathname();

  return (
    <ErrorBoundary key={pathname} title={title} description={description}>
      {children}
    </ErrorBoundary>
  );
}
