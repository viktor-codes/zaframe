import type { StudioPublicResponse, StudioResponse } from "./types";

type StudioProfile = Pick<
  StudioResponse,
  "name" | "slug" | "city" | "address" | "cover_url" | "logo_url" | "is_active"
>;

export function getStudioDisplayName(studio: Pick<StudioProfile, "name">): string {
  return studio.name.trim();
}

export function getStudioCoverUrl(
  studio: Pick<StudioProfile, "cover_url" | "logo_url">,
): string | null {
  return studio.cover_url ?? studio.logo_url ?? null;
}

export function getStudioLocationLabel(
  studio: Pick<StudioProfile, "city" | "address">,
): string | null {
  const parts = [studio.city, studio.address]
    .map((value) => value?.trim())
    .filter((value): value is string => Boolean(value));

  return parts.length > 0 ? parts.join(", ") : null;
}

export function hasStudioSlug(
  studio: Pick<StudioProfile, "slug">,
): studio is StudioProfile & { slug: string } {
  return typeof studio.slug === "string" && studio.slug.length > 0;
}

export function isStudioActive(studio: Pick<StudioProfile, "is_active">): boolean {
  return studio.is_active;
}

export function getPublicStudioServiceCount(
  studio: Pick<StudioPublicResponse, "services">,
): number {
  return studio.services?.length ?? 0;
}
