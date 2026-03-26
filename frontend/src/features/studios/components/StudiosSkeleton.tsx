"use client";

import { Skeleton } from "@/components/ui/Skeleton";

export function StudiosSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="overflow-hidden rounded-2xl border border-zinc-100 bg-white p-3"
        >
          <Skeleton className="aspect-9/10 w-full rounded-xl" />
          <div className="mt-4 space-y-2 px-1">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex justify-between border-t border-zinc-100 pt-3">
              <Skeleton className="h-5 w-12" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="mt-4 h-11 w-full rounded-xl" />
          </div>
        </div>
      ))}
    </div>
  );
}
