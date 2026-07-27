import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

export function MyStudiosSkeleton() {
  return <ResourceListSkeleton testId="my-studios-skeleton" rows={3} />;
}

export function MyStudiosErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <ResourceErrorState
      title="Could not load your studios"
      message={message}
      testId="my-studios-error"
      onRetry={onRetry}
    />
  );
}

export function MyStudiosEmptyState() {
  return (
    <ResourceEmptyState
      title="Create your first studio"
      description="Set up a studio profile, publish a service, and start taking bookings."
      testId="my-studios-empty"
      ctaHref="/dashboard/studios/new"
      ctaLabel="Create studio"
    />
  );
}
