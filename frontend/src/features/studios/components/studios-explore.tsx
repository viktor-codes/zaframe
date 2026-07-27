"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import { X, ChevronDown } from "lucide-react";
import Link from "next/link";

import {
  isServiceCategory,
  SERVICE_CATEGORIES,
  type ServiceCategory,
} from "@entities/service";
import type { PaginatedSearchResultList } from "@entities/studio";
import { Header } from "@features/navigation/components/Header";
import { fetchStudios, getUserFacingApiMessage } from "@shared/api";
import { queryKeys } from "@shared/lib/query-keys";
import { useUIStore } from "@shared/lib/ui-store";
import { Button } from "@shared/ui/button";

import {
  mergeExploreSearchResults,
  toStudiosExploreListParams,
  type StudiosExploreFilters,
} from "../model/explore-filters";
import { EmptyState } from "./EmptyState";
import { StudiosSearchBar } from "./StudiosSearchBar";
import { StudiosSkeleton } from "./StudiosSkeleton";
import { StudioSearchCard } from "./StudioSearchCard";

const CATEGORY_LABELS: Record<ServiceCategory, string> = {
  yoga: "Yoga",
  boxing: "Boxing",
  dance: "Dance",
  hiit: "HIIT",
  pilates: "Pilates",
  martial_arts: "Martial Arts",
  strength: "Strength",
};

const CATEGORIES: { value: ServiceCategory; label: string }[] =
  SERVICE_CATEGORIES.map((value) => ({
    value,
    label: CATEGORY_LABELS[value],
  }));

const AMENITIES_OPTIONS = [
  "parking",
  "shower",
  "lockers",
  "mat_rental",
  "wifi",
  "cafe",
];

export interface StudiosExploreProps {
  /** Server-fetched first page for the current URL filters (SEO + LCP). */
  initialPage?: PaginatedSearchResultList;
  /** True when the RSC prefetch failed; client query still retries. */
  initialFetchFailed?: boolean;
  /** Filters parsed on the server — kept for remount key alignment. */
  filters: StudiosExploreFilters;
}

export function StudiosExplore({
  initialPage,
  initialFetchFailed = false,
  filters: serverFilters,
}: StudiosExploreProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const categoryParam = searchParams.get("category") ?? "";
  const category = isServiceCategory(categoryParam) ? categoryParam : "";
  const city = searchParams.get("city") ?? "";
  const query = searchParams.get("query") ?? "";
  const amenitiesParam = searchParams.get("amenities");
  const amenities = useMemo(
    () => (amenitiesParam ? amenitiesParam.split(",").filter(Boolean) : []),
    [amenitiesParam],
  );
  const [categoriesOpen, setCategoriesOpen] = useState(true);

  const listParams = useMemo(
    () =>
      toStudiosExploreListParams({
        category,
        city,
        query,
        amenities,
      }),
    [category, city, query, amenities],
  );

  // WHY: only seed the cache when URL filters still match the RSC prefetch.
  const canUseInitialPage =
    initialPage != null &&
    !initialFetchFailed &&
    serverFilters.category === category &&
    serverFilters.city === city &&
    serverFilters.query === query &&
    serverFilters.amenities.join(",") === amenities.join(",");

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: queryKeys.studios.explore(listParams),
    queryFn: async ({ pageParam }) => {
      const page = await fetchStudios({ ...listParams, page: pageParam });
      return page as PaginatedSearchResultList;
    },
    initialPageParam: 1,
    initialData: canUseInitialPage
      ? { pages: [initialPage], pageParams: [1] }
      : undefined,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
    staleTime: 60_000,
    retry: (failureCount, err) => {
      const msg = err instanceof Error ? err.message.toLowerCase() : "";
      const isNetworkError =
        msg.includes("fetch") ||
        msg.includes("network") ||
        msg.includes("failed");
      return isNetworkError && failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 4000),
  });

  const results = useMemo(
    () => mergeExploreSearchResults(data?.pages ?? []),
    [data],
  );

  const loadMoreRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!hasNextPage || isFetchingNextPage) return;
    const el = loadMoreRef.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) fetchNextPage();
      },
      { rootMargin: "200px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [hasNextPage, isFetchingNextPage, fetchNextPage]);

  const updateSearch = useCallback(
    (newCategory: string, newCity: string) => {
      const next = new URLSearchParams(searchParams.toString());
      if (newCategory) next.set("category", newCategory);
      else next.delete("category");
      if (newCity) next.set("city", newCity);
      else next.delete("city");
      router.replace(`/studios?${next.toString()}`, { scroll: false });
    },
    [router, searchParams],
  );

  const toggleCategory = useCallback(
    (value: ServiceCategory) => {
      const next = new URLSearchParams(searchParams.toString());
      if (category === value) next.delete("category");
      else next.set("category", value);
      router.replace(`/studios?${next.toString()}`, { scroll: false });
    },
    [router, searchParams, category],
  );

  const toggleAmenity = useCallback(
    (a: string) => {
      const next = new URLSearchParams(searchParams.toString());
      const nextList = amenities.includes(a)
        ? amenities.filter((x) => x !== a)
        : [...amenities, a];
      if (nextList.length) next.set("amenities", nextList.join(","));
      else next.delete("amenities");
      router.replace(`/studios?${next.toString()}`, { scroll: false });
    },
    [router, searchParams, amenities],
  );

  const resetFilters = useCallback(() => {
    router.replace("/studios", { scroll: false });
  }, [router]);

  const hasFilters = category || city || query || amenities.length > 0;
  const setHeaderVariant = useUIStore((state) => state.setHeaderVariant);

  useEffect(() => {
    setHeaderVariant("on-light");
  }, [setHeaderVariant]);

  const showInitialLoading = isLoading && !canUseInitialPage;

  return (
    <div className="min-h-screen bg-white">
      <Header
        minimalSearch={{
          href: "#studios-search",
          placeholder: "Search studios…",
        }}
      />

      <div className="container mx-auto px-4 pt-28 pb-12">
        <nav
          className="mb-6 flex items-center gap-1.5 border-b border-zinc-100 pb-4 text-xs text-zinc-500"
          aria-label="Breadcrumb"
        >
          <Link href="/" className="transition-colors hover:text-zinc-700">
            Home
          </Link>
          <span aria-hidden>/</span>
          <span>Ireland</span>
          <span aria-hidden>/</span>
          <span className="font-medium text-zinc-900">Studios</span>
        </nav>

        <div className="mb-8">
          <StudiosSearchBar
            key={`${category}-${city}`}
            category={category}
            city={city}
            onSearch={updateSearch}
          />
        </div>

        <div className="mb-8 border-b border-zinc-100 pb-6">
          <button
            type="button"
            onClick={() => setCategoriesOpen((prev) => !prev)}
            className="flex w-full items-center justify-start gap-2 py-2 text-left text-sm font-semibold text-zinc-900"
            aria-expanded={categoriesOpen}
          >
            Categories
            <ChevronDown
              className={`h-4 w-4 text-zinc-500 transition-transform duration-200 ${
                categoriesOpen ? "rotate-180" : "rotate-0"
              }`}
            />
          </button>
          {categoriesOpen ? (
            <div className="overflow-hidden">
              <div className="flex flex-wrap gap-2 pt-2 pb-4">
                <button
                  type="button"
                  onClick={() => {
                    const next = new URLSearchParams(searchParams.toString());
                    next.delete("category");
                    router.replace(`/studios?${next.toString()}`, {
                      scroll: false,
                    });
                  }}
                  className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                    !category
                      ? "bg-zinc-900 text-white"
                      : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                  }`}
                >
                  All
                </button>
                {CATEGORIES.map(({ value, label }) => {
                  const isActive = category === value;
                  return (
                    <button
                      key={value}
                      type="button"
                      onClick={() => toggleCategory(value)}
                      className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-zinc-900 text-white"
                          : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                      }`}
                    >
                      {label}
                    </button>
                  );
                })}
              </div>
              <div className="border-t border-zinc-100 pt-4">
                <p className="mb-2 text-xs font-semibold tracking-wider text-zinc-500 uppercase">
                  Amenities
                </p>
                <div className="flex flex-wrap gap-2">
                  {AMENITIES_OPTIONS.map((a) => {
                    const isActive = amenities.includes(a);
                    return (
                      <button
                        key={a}
                        type="button"
                        onClick={() => toggleAmenity(a)}
                        className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                          isActive
                            ? "bg-zinc-900 text-white"
                            : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                        }`}
                      >
                        {a.replace("_", " ")}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : null}
          {hasFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={resetFilters}
              className="mt-2"
            >
              <X className="mr-1 h-4 w-4" />
              Clear filters
            </Button>
          )}
        </div>

        <main>
          {isError && (
            <div className="mb-8 flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800 sm:flex-row sm:items-center sm:justify-between">
              <span>{getUserFacingApiMessage(error)}</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => refetch()}
                className="shrink-0"
              >
                Try again
              </Button>
            </div>
          )}

          {showInitialLoading && <StudiosSkeleton />}

          {!showInitialLoading && !isError && results.length === 0 && (
            <EmptyState onReset={resetFilters} />
          )}

          {!showInitialLoading && !isError && results.length > 0 && (
            <>
              <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {results.map((result, index) => (
                  <StudioSearchCard
                    key={result.studio.id}
                    result={result}
                    index={index}
                  />
                ))}
              </div>
              <div ref={loadMoreRef} className="h-4 min-h-4" aria-hidden />
              {isFetchingNextPage && (
                <div className="mt-6 flex justify-center">
                  <span className="text-sm text-zinc-500">Loading more…</span>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
