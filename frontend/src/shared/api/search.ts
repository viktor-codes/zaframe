/**
 * API поиска студий и услуг.
 */

import { api } from "./client";
import type { SearchQueryParams, SearchResult } from "@entities/studio";

export async function fetchSearch(
  params: SearchQueryParams = {},
): Promise<SearchResult[]> {
  const searchParams: Record<
    string,
    string | number | boolean | undefined | string[]
  > = {};
  if (params.query != null && params.query !== "")
    searchParams.query = params.query;
  if (params.category != null) searchParams.category = params.category;
  if (params.city != null && params.city !== "")
    searchParams.city = params.city;
  if (params.lat != null) searchParams.lat = params.lat;
  if (params.lng != null) searchParams.lng = params.lng;
  if (params.radius_km != null) searchParams.radius_km = params.radius_km;
  if (params.amenities != null && params.amenities.length > 0)
    searchParams.amenities = params.amenities;

  return api.get<SearchResult[]>("api/v1/search", {
    params: searchParams,
    skipAuth: true,
  });
}
