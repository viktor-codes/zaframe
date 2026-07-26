import Link from "next/link";
import { Button, Skeleton } from "@shared/ui";

export function OrdersErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-red-800"
      data-testid="orders-error"
    >
      <p className="font-medium">Could not load orders</p>
      <p className="mt-1 text-sm">{message}</p>
      <Button type="button" className="mt-4" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

export function OrdersEmptyState() {
  return (
    <div
      className="rounded-2xl border border-neutral-200 bg-white p-10 text-center"
      data-testid="orders-empty"
    >
      <p className="font-display text-lg font-semibold text-neutral-900">
        No course orders yet
      </p>
      <p className="mt-2 text-sm text-neutral-600">
        When you book a multi-session course, the order and payment status show
        up here.
      </p>
      <Button asChild className="mt-5">
        <Link href="/studios">Browse studios</Link>
      </Button>
    </div>
  );
}

export function OrdersSkeleton() {
  return (
    <div className="space-y-3" data-testid="orders-loading">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="rounded-2xl border border-neutral-200 bg-white p-4"
        >
          <div className="space-y-2">
            <Skeleton className="h-5 w-48" />
            <Skeleton className="h-4 w-40" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}
