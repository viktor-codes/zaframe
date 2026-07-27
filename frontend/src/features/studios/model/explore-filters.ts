import {
  isServiceCategory,
  type ServiceCategory,
} from "@entities/service";
import type {
  PaginatedSearchResultList,
  SearchResult,
  StudiosListParams,
} from "@entities/studio";

export const STUDIOS_EXPLORE_PAGE_SIZE = 12;

export interface StudiosExploreFilters {
  category: ServiceCategory | "";
  city: string;
  query: string;
  amenities: string[];
}

function firstSearchParam(
  value: string | string[] | undefined,
): string {
  if (Array.isArray(value)) return value[0] ?? "";
  return value ?? "";
}

/**
 * Parse `/studios` searchParams into typed explore filters.
 */
export function parseStudiosExploreFilters(
  searchParams: Record<string, string | string[] | undefined>,
): StudiosExploreFilters {
  const categoryRaw = firstSearchParam(searchParams.category);
  const amenitiesRaw = firstSearchParam(searchParams.amenities);

  return {
    category: isServiceCategory(categoryRaw) ? categoryRaw : "",
    city: firstSearchParam(searchParams.city).trim(),
    query: firstSearchParam(searchParams.query).trim(),
    amenities: amenitiesRaw
      ? amenitiesRaw.split(",").map((item) => item.trim()).filter(Boolean)
      : [],
  };
}

/** Stable key for remounting the explore island when URL filters change. */
export function studiosExploreFiltersKey(
  filters: StudiosExploreFilters,
): string {
  return [
    filters.category,
    filters.city,
    filters.query,
    filters.amenities.join(","),
  ].join("|");
}

export function toStudiosExploreListParams(
  filters: StudiosExploreFilters,
): StudiosListParams {
  return {
    is_active: true,
    size: STUDIOS_EXPLORE_PAGE_SIZE,
    include_services: true,
    ...(filters.category ? { category: filters.category } : {}),
    ...(filters.city ? { city: filters.city } : {}),
    ...(filters.query ? { query: filters.query } : {}),
    ...(filters.amenities.length > 0
      ? { amenities: filters.amenities }
      : {}),
  };
}

/**
 * Flatten infinite-query pages and merge duplicate studios by id
 * (matched services union).
 */
export function mergeExploreSearchResults(
  pages: readonly PaginatedSearchResultList[],
): SearchResult[] {
  const items = pages.flatMap((page) => page.items);
  const byStudioId = new Map<number, SearchResult>();

  for (const item of items) {
    const existing = byStudioId.get(item.studio.id);
    if (!existing) {
      byStudioId.set(item.studio.id, {
        ...item,
        matched_services: [...(item.matched_services ?? [])],
      });
      continue;
    }

    const mergedById = new Map<
      number,
      SearchResult["matched_services"][number]
    >();
    for (const service of existing.matched_services ?? []) {
      mergedById.set(service.id, service);
    }
    for (const service of item.matched_services ?? []) {
      mergedById.set(service.id, service);
    }
    existing.matched_services = Array.from(mergedById.values());
  }

  return Array.from(byStudioId.values());
}
