"use client";

import { Suspense, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { fetchStudio } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { Skeleton } from "@shared/ui";

/**
 * Legacy `/studios/[id]` → Phase 3 slug storefront.
 * Kept so old explore links and bookmarks land on `/s/{slug}`.
 */
function LegacyStudioRedirect() {
  const router = useRouter();
  const params = useParams();
  const studioId = Number(params.id);
  const isValidStudio = Number.isInteger(studioId) && studioId > 0;

  const { data: studio, isError: studioError } = useQuery({
    queryKey: queryKeys.studio.detail(studioId),
    queryFn: () => fetchStudio(studioId),
    enabled: isValidStudio,
    retry: false,
  });

  useEffect(() => {
    if (!isValidStudio) return;
    if (studioError) {
      router.replace("/studios");
      return;
    }
    if (!studio) return;

    const slug = studio.slug?.trim();
    if (!slug) {
      return;
    }
    router.replace(`/s/${encodeURIComponent(slug)}`);
  }, [isValidStudio, router, studio, studioError]);

  if (!isValidStudio) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Invalid studio</p>
          <Link
            href="/studios"
            className="mt-2 inline-block text-primary underline"
          >
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (studioError) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Studio not found</p>
          <Link
            href="/studios"
            className="mt-2 inline-block text-primary underline"
          >
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (studio && !studio.slug?.trim()) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-900">
          <p className="font-semibold">{studio.name}</p>
          <p className="mt-2 text-sm">
            This studio does not have a public page yet. Ask the owner to set a
            slug before booking is available.
          </p>
          <Link
            href="/studios"
            className="mt-3 inline-block text-primary underline"
          >
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl space-y-3 px-6 py-12">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-40 w-full" />
      <p className="text-sm text-neutral-500">Opening studio page…</p>
    </div>
  );
}

export default function StudioDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl space-y-3 px-6 py-12">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-40 w-full" />
        </div>
      }
    >
      <LegacyStudioRedirect />
    </Suspense>
  );
}
