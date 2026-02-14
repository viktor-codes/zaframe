"use client";

import { Skeleton } from "@/components/ui/Skeleton";

export function StudiosSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="rounded-2xl overflow-hidden bg-white border border-zinc-100 p-3">
          <Skeleton className="aspect-9/10 w-full rounded-xl" />
          <div className="mt-4 px-1 space-y-2">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex justify-between pt-3 border-t border-zinc-100">
              <Skeleton className="h-5 w-12" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-11 w-full rounded-xl mt-4" />
          </div>
        </div>
      ))}
    </div>
  );
}
