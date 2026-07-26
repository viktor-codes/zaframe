import { Skeleton } from "@shared/ui";

export default function StudioStorefrontLoading() {
  return (
    <div
      className="mx-auto max-w-3xl px-4 pt-28 pb-16 sm:px-6"
      data-testid="studio-storefront-loading"
    >
      <Skeleton className="mb-6 h-3 w-40" />
      <Skeleton className="mb-6 aspect-16/10 w-full rounded-2xl" />
      <div className="mb-10 flex gap-4">
        <Skeleton className="h-16 w-16 shrink-0 rounded-xl sm:h-20 sm:w-20" />
        <div className="flex-1 space-y-3">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-4/5" />
        </div>
      </div>
      <Skeleton className="mb-4 h-6 w-24" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="overflow-hidden rounded-2xl bg-white p-3 shadow-paper"
          >
            <Skeleton className="aspect-4/5 w-full rounded-xl" />
            <Skeleton className="mt-4 h-5 w-3/4" />
            <Skeleton className="mt-2 h-3 w-1/3" />
          </div>
        ))}
      </div>
    </div>
  );
}
