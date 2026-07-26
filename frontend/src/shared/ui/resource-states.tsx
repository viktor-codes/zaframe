import Link from "next/link";
import { Button } from "./button";
import { Skeleton } from "./skeleton";

export interface ResourceEmptyStateProps {
  title: string;
  description: string;
  testId: string;
  ctaHref?: string;
  ctaLabel?: string;
}

/** JTBD empty surface for account / list screens. */
export function ResourceEmptyState({
  title,
  description,
  testId,
  ctaHref,
  ctaLabel,
}: ResourceEmptyStateProps) {
  return (
    <div
      className="rounded-2xl border border-neutral-200 bg-white p-10 text-center"
      data-testid={testId}
    >
      <p className="font-display text-lg font-semibold text-neutral-900">
        {title}
      </p>
      <p className="mt-2 text-sm text-neutral-600">{description}</p>
      {ctaHref && ctaLabel ? (
        <Button asChild className="mt-5">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </Button>
      ) : null}
    </div>
  );
}

export interface ResourceErrorStateProps {
  title: string;
  message: string;
  testId: string;
  onRetry: () => void;
}

/** Retryable load error for list screens. */
export function ResourceErrorState({
  title,
  message,
  testId,
  onRetry,
}: ResourceErrorStateProps) {
  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-red-800"
      data-testid={testId}
    >
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm">{message}</p>
      <Button type="button" className="mt-4" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

export interface ResourceListSkeletonProps {
  testId: string;
  rows?: number;
}

/** Card-shaped placeholder rows for paginated lists. */
export function ResourceListSkeleton({
  testId,
  rows = 3,
}: ResourceListSkeletonProps) {
  return (
    <div className="space-y-3" data-testid={testId}>
      {Array.from({ length: rows }).map((_, index) => (
        <div
          key={index}
          className="rounded-2xl border border-neutral-200 bg-white p-4"
        >
          <div className="space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}
