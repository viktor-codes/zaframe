/**
 * Типы для поиска студий и услуг.
 */

import type { ServiceResponse } from "./service";
import type { StudioResponse } from "./studio";

export interface SearchResult {
  studio: StudioResponse;
  matched_services: ServiceResponse[];
}

export interface SearchQueryParams {
  query?: string | null;
  category?: string | null;
  city?: string | null;
  lat?: number | null;
  lng?: number | null;
  radius_km?: number | null;
  amenities?: string[] | null;
}
