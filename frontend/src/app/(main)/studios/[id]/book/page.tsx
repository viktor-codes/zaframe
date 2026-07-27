import Link from "next/link";
import { redirect } from "next/navigation";

import { ApiError } from "@shared/api/api-error";
import {
  fetchPublicServiceOccurrences,
  fetchStudioById,
  fetchStudioPublicBySlug,
} from "@shared/api/server";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface LegacyBookPageProps {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ occurrence?: string }>;
}

/**
 * Resolve bookable service id for a legacy `?occurrence=` deep link via public APIs.
 */
async function findServiceIdForOccurrence(
  slug: string,
  occurrenceId: number,
): Promise<number | null> {
  const publicStudio = await fetchStudioPublicBySlug(slug);
  const services = publicStudio.services ?? [];

  const matches = await Promise.all(
    services.map(async (service) => {
      const occurrences = await fetchPublicServiceOccurrences(slug, service.id);
      return occurrences.some((item) => item.id === occurrenceId)
        ? service.id
        : null;
    }),
  );

  return matches.find((serviceId): serviceId is number => serviceId != null) ?? null;
}

/**
 * Legacy `/studios/[id]/book` → Phase 3 slug storefront wizard.
 * Kept as a redirect so old links and emails do not create holds without Stripe.
 */
export default async function BookPage({
  params,
  searchParams,
}: LegacyBookPageProps) {
  const { id } = await params;
  const { occurrence: occurrenceParam } = await searchParams;
  const studioId = parsePositiveIdString(id);
  const occurrenceId = parsePositiveIdString(occurrenceParam ?? null);

  if (studioId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <p className="text-sm text-neutral-600">Invalid studio link.</p>
        <Link href="/studios" className="mt-3 inline-block text-primary underline">
          Browse studios
        </Link>
      </div>
    );
  }

  let studio;
  try {
    studio = await fetchStudioById(studioId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      redirect("/studios");
    }
    throw error;
  }

  const slug = studio.slug?.trim();
  if (!slug) {
    redirect(`/studios/${studioId}`);
  }

  if (occurrenceId != null) {
    const serviceId = await findServiceIdForOccurrence(slug, occurrenceId);
    if (serviceId != null) {
      redirect(`/s/${encodeURIComponent(slug)}/book/${serviceId}`);
    }
  }

  redirect(`/s/${encodeURIComponent(slug)}`);
}
