import Image from "next/image";
import { getStudioCoverUrl, getStudioDisplayName } from "../model/studio";
import type { StudioPublicResponse } from "../model/types";

export interface StudioGalleryProps {
  studio: Pick<StudioPublicResponse, "name" | "cover_url" | "logo_url">;
  className?: string;
}

/**
 * Public storefront media strip.
 * API currently exposes cover + logo only — no multi-photo gallery yet.
 */
export function StudioGallery({ studio, className = "" }: StudioGalleryProps) {
  const name = getStudioDisplayName(studio);
  const coverUrl = getStudioCoverUrl(studio);
  const hasDistinctLogo =
    Boolean(studio.logo_url) &&
    Boolean(studio.cover_url) &&
    studio.logo_url !== studio.cover_url;

  return (
    <div
      className={`overflow-hidden rounded-2xl border border-neutral-200 bg-neutral-100 ${className}`}
      data-testid="studio-gallery"
    >
      <div className="relative aspect-16/10 w-full sm:aspect-21/9">
        {coverUrl ? (
          <Image
            src={coverUrl}
            alt={`${name} cover`}
            fill
            priority
            className="object-cover"
            sizes="(max-width: 768px) 100vw, 960px"
            unoptimized={coverUrl.startsWith("http")}
          />
        ) : (
          <div
            className="absolute inset-0 bg-linear-to-br from-sky-100 via-teal-50 to-lime-100"
            aria-hidden
          />
        )}

        {hasDistinctLogo && studio.logo_url ? (
          <div className="absolute bottom-3 left-3 h-14 w-14 overflow-hidden rounded-xl border-2 border-white bg-white shadow-md sm:bottom-4 sm:left-4 sm:h-16 sm:w-16">
            <Image
              src={studio.logo_url}
              alt={`${name} logo`}
              fill
              className="object-cover"
              sizes="64px"
              unoptimized={studio.logo_url.startsWith("http")}
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
