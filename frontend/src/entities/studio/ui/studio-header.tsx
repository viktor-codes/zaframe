import Image from "next/image";
import { getStudioDisplayName } from "../model/studio";
import type { StudioPublicResponse } from "../model/types";

export interface StudioHeaderProps {
  studio: Pick<
    StudioPublicResponse,
    "name" | "description" | "logo_url" | "slug"
  >;
  className?: string;
}

export function StudioHeader({ studio, className = "" }: StudioHeaderProps) {
  const name = getStudioDisplayName(studio);
  const logoUrl = studio.logo_url?.trim() || null;
  const description = studio.description?.trim() || null;

  return (
    <header
      className={`flex flex-col gap-4 sm:flex-row sm:items-start sm:gap-6 ${className}`}
      data-testid="studio-header"
    >
      <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-xl border border-neutral-200 bg-neutral-100 sm:h-20 sm:w-20">
        {logoUrl ? (
          <Image
            src={logoUrl}
            alt={`${name} logo`}
            fill
            className="object-cover"
            sizes="80px"
            unoptimized={logoUrl.startsWith("http")}
          />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center bg-linear-to-br from-sky-100 via-teal-50 to-lime-100 font-display text-xl font-bold text-teal-700"
            aria-hidden
          >
            {name.slice(0, 1).toUpperCase()}
          </div>
        )}
      </div>

      <div className="min-w-0 flex-1">
        <h1 className="font-display text-2xl font-bold tracking-tight text-neutral-900 sm:text-3xl">
          {name}
        </h1>
        {description ? (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-neutral-600 sm:text-base">
            {description}
          </p>
        ) : null}
      </div>
    </header>
  );
}
