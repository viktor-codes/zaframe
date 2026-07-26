"use client";

import { Suspense, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { fetchStudio, fetchStudioOccurrences } from "@shared/api";
import { OccurrenceStatus, queryKeys } from "@shared/lib";
import { Skeleton } from "@shared/ui";

/**
 * Legacy `/studios/[id]/book` → Phase 3 slug storefront wizard.
 * Kept as a redirect so old links and emails do not create holds without Stripe.
 */
function LegacyBookRedirect() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();
  const studioId = Number(params.id);
  const occurrenceIdParam = searchParams.get("occurrence");
  const occurrenceId = occurrenceIdParam ? Number(occurrenceIdParam) : null;

  const isValidStudio = Number.isInteger(studioId) && studioId > 0;

  const { data: studio, isError: studioError } = useQuery({
    queryKey: queryKeys.studio.detail(studioId),
    queryFn: () => fetchStudio(studioId),
    enabled: isValidStudio,
    retry: false,
  });

  const { data: occurrences, isFetched: occurrencesFetched } = useQuery({
    queryKey: queryKeys.studio.occurrences(studioId, {
      status: OccurrenceStatus.SCHEDULED,
    }),
    queryFn: () =>
      fetchStudioOccurrences(studioId, {
        status: OccurrenceStatus.SCHEDULED,
      }),
    enabled: isValidStudio && Boolean(studio),
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
      router.replace(`/studios/${studioId}`);
      return;
    }

    if (occurrenceId != null && Number.isInteger(occurrenceId)) {
      if (!occurrencesFetched) return;
      const occurrence = occurrences?.find((item) => item.id === occurrenceId);
      if (occurrence) {
        router.replace(
          `/s/${encodeURIComponent(slug)}/book/${occurrence.service_id}`,
        );
        return;
      }
    }

    router.replace(`/s/${encodeURIComponent(slug)}`);
  }, [
    isValidStudio,
    studio,
    studioError,
    studioId,
    occurrenceId,
    occurrences,
    occurrencesFetched,
    router,
  ]);

  if (!isValidStudio) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <p className="text-sm text-neutral-600">Invalid studio link.</p>
        <Link href="/studios" className="mt-3 inline-block text-primary underline">
          Browse studios
        </Link>
      </div>
    );
  }

  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="legacy-book-redirect"
    >
      <Skeleton className="h-48 w-full" />
      <p className="mt-4 text-center text-sm text-neutral-500">
        Taking you to the booking page…
      </p>
    </div>
  );
}

export default function BookPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-6 py-12">
          <Skeleton className="h-64 w-full" />
        </div>
      }
    >
      <LegacyBookRedirect />
    </Suspense>
  );
}
