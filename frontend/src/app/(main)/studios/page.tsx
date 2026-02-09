"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card, Button, Skeleton } from "@/components/ui";
import {
  fetchStudios,
  fetchStudiosCount,
} from "@/lib/api";

const PAGE_SIZE = 12;

export default function StudiosPage() {
  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <h1 className="font-display font-bold text-3xl text-secondary mb-2">
        Studios
      </h1>
      <p className="text-neutral-600 mb-8">
        Browse available photography and video studios. Choose a studio to view
        schedule and book a session.
      </p>
      <StudiosList />
    </div>
  );
}

function StudiosList() {
  const [page, setPage] = useState(0);
  const skip = page * PAGE_SIZE;

  const {
    data: studios,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["studios", skip, PAGE_SIZE],
    queryFn: () => fetchStudios({ skip, limit: PAGE_SIZE, is_active: true }),
  });

  const { data: countData } = useQuery({
    queryKey: ["studios", "count", true],
    queryFn: () => fetchStudiosCount({ is_active: true }),
  });

  const totalCount = countData?.count ?? 0;
  const totalPages = Math.ceil(totalCount / PAGE_SIZE);
  const hasNext = page < totalPages - 1;
  const hasPrev = page > 0;

  if (isError) {
    return (
      <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
        <p className="font-semibold">Failed to load studios</p>
        <p className="text-sm mt-1">
          {error instanceof Error ? error.message : "Unknown error"}
        </p>
      </div>
    );
  }

  if (isLoading) {
    return <StudiosSkeleton />;
  }

  if (!studios || studios.length === 0) {
    return (
      <div className="rounded-lg bg-neutral-100 border border-neutral-200 p-12 text-center text-neutral-600">
        <p className="font-medium">No studios available yet</p>
        <p className="text-sm mt-1">Check back later for new studios.</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {studios.map((studio) => (
          <Link key={studio.id} href={`/studios/${studio.id}`}>
            <Card variant="interactive" className="h-full">
              <div className="space-y-3">
                <h2 className="font-display font-semibold text-lg text-secondary">
                  {studio.name}
                </h2>
                {studio.description && (
                  <p className="text-neutral-600 text-sm line-clamp-3">
                    {studio.description}
                  </p>
                )}
                {studio.address && (
                  <p className="text-neutral-500 text-sm truncate">
                    {studio.address}
                  </p>
                )}
                <div className="pt-2">
                  <span className="text-primary text-sm font-medium hover:underline">
                    View schedule →
                  </span>
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <nav
          className="mt-10 flex items-center justify-center gap-4"
          aria-label="Pagination"
        >
          <Button
            variant="outline"
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={!hasPrev}
          >
            Previous
          </Button>
          <span className="text-neutral-600 text-sm">
            Page {page + 1} of {totalPages}
          </span>
          <Button
            variant="outline"
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={!hasNext}
          >
            Next
          </Button>
        </nav>
      )}
    </>
  );
}

function StudiosSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <div className="space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-2/3" />
            <Skeleton className="h-4 w-1/3 mt-4" />
          </div>
        </Card>
      ))}
    </div>
  );
}
