"use client";

import {
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useUIStore } from "@/store/useUIStore";
import { useRouter, useSearchParams } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import { X, ChevronDown } from "lucide-react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { fetchStudios } from "@/lib/api/studios";
import type { SearchResult } from "@/types/search";
import type { ServiceCategory } from "@/types/service";
import { Header } from "@/features/navigation/components";
import {
  StudioSearchCard,
  StudiosSearchBar,
  StudiosSkeleton,
  EmptyState,
} from "@/features/studios/components";
import { Button } from "@/components/ui/Button";

const PAGE_SIZE = 12;

const CATEGORIES: { value: ServiceCategory; label: string }[] = [
  { value: "yoga", label: "Yoga" },
  { value: "boxing", label: "Boxing" },
  { value: "dance", label: "Dance" },
  { value: "hiit", label: "HIIT" },
  { value: "pilates", label: "Pilates" },
  { value: "martial_arts", label: "Martial Arts" },
  { value: "strength", label: "Strength" },
];

const AMENITIES_OPTIONS = [
  "parking",
  "shower",
  "lockers",
  "mat_rental",
  "wifi",
  "cafe",
];

function StudiosPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const category = searchParams.get("category") ?? "";
  const city = searchParams.get("city") ?? "";
  const query = searchParams.get("query") ?? "";
  const amenitiesParam = searchParams.get("amenities");
  const amenities = useMemo(
    () => (amenitiesParam ? amenitiesParam.split(",").filter(Boolean) : []),
    [amenitiesParam],
  );
  const [categoriesOpen, setCategoriesOpen] = useState(true);

  const listParams = useMemo(
    () => ({
      is_active: true,
      limit: PAGE_SIZE,
      include_services: true,
      ...(category && { category }),
      ...(city && { city }),
      ...(query && { query }),
      ...(amenities.length > 0 && { amenities }),
    }),
    [category, city, query, amenities],
  );

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
    queryKey: ["studios", "explore", listParams],
    queryFn: ({ pageParam }) =>
      fetchStudios({ ...listParams, skip: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage, _allPages, lastPageParam) =>
      lastPage.length < PAGE_SIZE
        ? undefined
        : (lastPageParam as number) + PAGE_SIZE,
    staleTime: 60_000,
    retry: (failureCount, err) => {
      const msg = err instanceof Error ? err.message.toLowerCase() : "";
      const isNetworkError =
        msg.includes("fetch") || msg.includes("network") || msg.includes("failed");
      return isNetworkError && failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 4000),
  });

  const results: SearchResult[] = useMemo(
    () => data?.pages.flat() ?? [],
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

  const toggleCategory = useCallback((value: ServiceCategory) => {
    const next = new URLSearchParams(searchParams.toString());
    if (category === value) next.delete("category");
    else next.set("category", value);
    router.replace(`/studios?${next.toString()}`, { scroll: false });
  }, [router, searchParams, category]);

  const toggleAmenity = useCallback((a: string) => {
    const next = new URLSearchParams(searchParams.toString());
    const nextList = amenities.includes(a)
      ? amenities.filter((x) => x !== a)
      : [...amenities, a];
    if (nextList.length) next.set("amenities", nextList.join(","));
    else next.delete("amenities");
    router.replace(`/studios?${next.toString()}`, { scroll: false });
  }, [router, searchParams, amenities]);

  const resetFilters = useCallback(() => {
    router.replace("/studios", { scroll: false });
  }, [router]);

  const hasFilters = category || city || query || amenities.length > 0;
  const setHeaderVariant = useUIStore((state) => state.setHeaderVariant);

  useEffect(() => {
    setHeaderVariant("on-light");
  }, [setHeaderVariant]);

  return (
    <div className="min-h-screen bg-white">
      <Header
        minimalSearch={{ href: "#studios-search", placeholder: "Search studios…" }}
      />

      <div className="container mx-auto px-4 pt-28 pb-12">
        <nav className="flex items-center gap-1.5 text-xs text-zinc-500 mb-6 border-b border-zinc-100 pb-4" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-zinc-700 transition-colors">
            Home
          </Link>
          <span aria-hidden>/</span>
          <span>Ireland</span>
          <span aria-hidden>/</span>
          <span className="text-zinc-900 font-medium">Studios</span>
        </nav>

        <div className="mb-8">
          <StudiosSearchBar
            key={`${category}-${city}`}
            category={category}
            city={city}
            onSearch={updateSearch}
          />
        </div>

        <div className="border-b border-zinc-100 pb-6 mb-8">
          <button
            type="button"
            onClick={() => setCategoriesOpen((prev) => !prev)}
            className="flex items-center gap-2 w-full text-left py-2 text-sm font-semibold text-zinc-900"
          >
            Categories
            <motion.span
              animate={{ rotate: categoriesOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="w-4 h-4 text-zinc-500" />
            </motion.span>
          </button>
          <AnimatePresence initial={false}>
            {categoriesOpen && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="overflow-hidden"
              >
                <div className="flex flex-wrap gap-2 pt-2 pb-4">
                  <button
                    type="button"
                    onClick={() => {
                      const next = new URLSearchParams(searchParams.toString());
                      next.delete("category");
                      router.replace(`/studios?${next.toString()}`, { scroll: false });
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
                  <p className="text-xs font-semibold uppercase tracking-wider text-zinc-500 mb-2">
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
              </motion.div>
            )}
          </AnimatePresence>
          {hasFilters && (
            <Button variant="ghost" size="sm" onClick={resetFilters} className="mt-2">
              <X className="w-4 h-4 mr-1" />
              Clear filters
            </Button>
          )}
        </div>

        <main>
          {isError && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-800 text-sm mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <span>
                {error instanceof Error
                  ? error.message
                  : "Failed to load results"}
              </span>
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

          {isLoading && <StudiosSkeleton />}

          {!isLoading && !isError && results.length === 0 && (
            <EmptyState onReset={resetFilters} />
          )}

          {!isLoading && !isError && results.length > 0 && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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

export default function StudiosPage() {
  return (
    <Suspense fallback={<StudiosSkeleton />}>
      <StudiosPageContent />
    </Suspense>
  );
}
