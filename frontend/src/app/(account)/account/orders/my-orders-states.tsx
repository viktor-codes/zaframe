import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

export function OrdersErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <ResourceErrorState
      title="Could not load orders"
      message={message}
      testId="orders-error"
      onRetry={onRetry}
    />
  );
}

export function OrdersEmptyState() {
  return (
    <ResourceEmptyState
      title="No course orders yet"
      description="When you book a multi-session course, the order and payment status show up here."
      ctaHref="/studios"
      ctaLabel="Browse studios"
      testId="orders-empty"
    />
  );
}

export function OrdersSkeleton() {
  return <ResourceListSkeleton testId="orders-loading" rows={3} />;
}
