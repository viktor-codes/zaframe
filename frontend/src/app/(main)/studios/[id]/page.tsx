import Link from "next/link";
import { redirect } from "next/navigation";

import { ApiError } from "@shared/api/api-error";
import { fetchStudioById } from "@shared/api/server";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface LegacyStudioPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Legacy `/studios/[id]` → Phase 3 slug storefront.
 * Kept so old explore links and bookmarks land on `/s/{slug}`.
 */
export default async function StudioDetailPage({
  params,
}: LegacyStudioPageProps) {
  const { id } = await params;
  const studioId = parsePositiveIdString(id);

  if (studioId == null) {
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

  redirect(`/s/${encodeURIComponent(slug)}`);
}
