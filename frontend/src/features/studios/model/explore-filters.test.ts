import { describe, expect, it } from "vitest";

import type { PaginatedSearchResultList, SearchResult } from "@entities/studio";

import {
  mergeExploreSearchResults,
  parseStudiosExploreFilters,
  studiosExploreFiltersKey,
  toStudiosExploreListParams,
} from "./explore-filters";

function searchResult(
  studioId: number,
  serviceIds: number[],
): SearchResult {
  return {
    studio: { id: studioId, name: `Studio ${studioId}` },
    matched_services: serviceIds.map((id) => ({
      id,
      studio_id: studioId,
      name: `Service ${id}`,
      category: "yoga",
      type: "single",
      duration_minutes: 60,
      max_capacity: 10,
      price_single_cents: 1000,
      soft_limit_ratio: 1,
      hard_limit_ratio: 1.5,
      max_overbooked_ratio: 0.3,
    })),
  } as SearchResult;
}

describe("parseStudiosExploreFilters", () => {
  it("parses category, city, query, and amenities", () => {
    expect(
      parseStudiosExploreFilters({
        category: "yoga",
        city: " Dublin ",
        query: " flow ",
        amenities: "parking,wifi",
      }),
    ).toEqual({
      category: "yoga",
      city: "Dublin",
      query: "flow",
      amenities: ["parking", "wifi"],
    });
  });

  it("drops unknown category", () => {
    expect(parseStudiosExploreFilters({ category: "nope" }).category).toBe("");
  });
});

describe("toStudiosExploreListParams", () => {
  it("always sets explore defaults", () => {
    expect(
      toStudiosExploreListParams({
        category: "",
        city: "",
        query: "",
        amenities: [],
      }),
    ).toEqual({
      is_active: true,
      size: 12,
      include_services: true,
    });
  });
});

describe("studiosExploreFiltersKey", () => {
  it("joins filter fields", () => {
    expect(
      studiosExploreFiltersKey({
        category: "yoga",
        city: "Dublin",
        query: "",
        amenities: ["wifi"],
      }),
    ).toBe("yoga|Dublin||wifi");
  });
});

describe("mergeExploreSearchResults", () => {
  it("merges matched services for the same studio across pages", () => {
    const page1 = {
      items: [searchResult(1, [10])],
      total: 2,
      page: 1,
      size: 1,
    } as PaginatedSearchResultList;
    const page2 = {
      items: [searchResult(1, [20]), searchResult(2, [30])],
      total: 2,
      page: 2,
      size: 1,
    } as PaginatedSearchResultList;

    const merged = mergeExploreSearchResults([page1, page2]);
    expect(merged).toHaveLength(2);
    expect(merged[0]?.matched_services.map((s) => s.id).sort()).toEqual([
      10, 20,
    ]);
    expect(merged[1]?.studio.id).toBe(2);
  });
});
