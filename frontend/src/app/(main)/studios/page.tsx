"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, X, ChevronDown } from "lucide-react";
import Link from "next/link";
import { fetchSearch } from "@/lib/api";
import type { SearchQueryParams } from "@/types/search";
import type { ServiceCategory } from "@/types/service";
import { StudioSearchCard } from "@/components/StudioSearchCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";
import { Header } from "@/components/Header";
import { motion, AnimatePresence } from "framer-motion";

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

function StudiosSearchBar({
  category,
  city,
  onSearch,
}: {
  category: string;
  city: string;
  onSearch: (category: string, city: string) => void;
}) {
  const [localCategory, setLocalCategory] = useState(category);
  const [localCity, setLocalCity] = useState(city);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localCategory, localCity);
  };

  return (
    <form
      id="studios-search"
      onSubmit={handleSubmit}
      className="flex flex-col sm:flex-row w-full max-w-3xl rounded-2xl bg-white border border-zinc-100 shadow-[0_1px_3px_rgba(0,0,0,0.04)] transition-shadow duration-200 hover:shadow-(--shadow-soft) overflow-hidden"
    >
      <div className="flex-1 flex items-center gap-2.5 px-4 py-3 min-w-0">
        <Search className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="Category (yoga, boxing…)"
          value={localCategory}
          onChange={(e) => setLocalCategory(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm font-medium text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <div className="hidden sm:block w-px bg-zinc-100 self-stretch shrink-0" aria-hidden />
      <div className="flex-1 flex items-center gap-2.5 px-4 py-3 min-w-0 border-t sm:border-t-0 sm:border-l border-zinc-100">
        <MapPin className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="City"
          value={localCity}
          onChange={(e) => setLocalCity(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm font-medium text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <div className="px-3 py-2.5 sm:py-2 border-t sm:border-t-0 border-zinc-100 shrink-0">
        <Button type="submit" size="md" className="w-full sm:w-auto">
          Search
        </Button>
      </div>
    </form>
  );
}

function StudiosSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="rounded-2xl overflow-hidden bg-white border border-zinc-100 p-3">
          <Skeleton className="aspect-9/10 w-full rounded-xl" />
          <div className="mt-4 px-1 space-y-2">
            <Skeleton className="h-6 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex justify-between pt-3 border-t border-zinc-100">
              <Skeleton className="h-5 w-12" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-11 w-full rounded-xl mt-4" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center py-24 px-6 text-center"
    >
      <div className="w-12 h-px bg-zinc-200 mb-8" aria-hidden />
      <p className="text-2xl md:text-3xl font-serif italic font-light text-zinc-700 tracking-tight max-w-lg">
        The vibe you&apos;re looking for is currently off the radar.
      </p>
      <p className="text-zinc-500 mt-4 text-sm max-w-md">
        Try another city or category, or clear filters to see all studios.
      </p>
      <Button variant="secondary" className="mt-8" onClick={onReset}>
        Clear filters
      </Button>
    </motion.div>
  );
}

export default function StudiosPage() {
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

  const params: SearchQueryParams = useMemo(
    () => ({
      ...(category && { category: category as ServiceCategory }),
      ...(city && { city }),
      ...(query && { query }),
      ...(amenities.length > 0 && { amenities }),
    }),
    [category, city, query, amenities],
  );

  const {
    data: results,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["search", params],
    queryFn: () => fetchSearch(params),
    staleTime: 60_000,
    retry: (failureCount, err) => {
      // Повторяем при сетевых ошибках (две вкладки, гонка с бэкендом)
      const msg = err instanceof Error ? err.message.toLowerCase() : "";
      const isNetworkError =
        msg.includes("fetch") || msg.includes("network") || msg.includes("failed");
      return isNetworkError && failureCount < 3;
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 4000),
  });

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

  return (
    <div className="min-h-screen bg-white">
      <Header
        variant="light"
        minimalSearch={{ href: "#studios-search", placeholder: "Search studios…" }}
      />

      <div className="container mx-auto px-4 pt-28 pb-12">
        {/* Breadcrumbs: Home / Ireland / Studios */}
        <nav className="flex items-center gap-1.5 text-xs text-zinc-500 mb-6 border-b border-zinc-100 pb-4" aria-label="Breadcrumb">
          <Link href="/" className="hover:text-zinc-700 transition-colors">
            Home
          </Link>
          <span aria-hidden>/</span>
          <span>Ireland</span>
          <span aria-hidden>/</span>
          <span className="text-zinc-900 font-medium">Studios</span>
        </nav>

        {/* Main search — key resets local state when URL changes */}
        <div className="mb-8">
          <StudiosSearchBar
            key={`${category}-${city}`}
            category={category}
            city={city}
            onSearch={updateSearch}
          />
        </div>

        {/* Filters: collapsible Categories + Amenities pills */}
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

        {/* Results */}
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

          {!isLoading && !isError && results && results.length === 0 && (
            <EmptyState onReset={resetFilters} />
          )}

          {!isLoading && !isError && results && results.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {results.map((result, index) => (
                <StudioSearchCard
                  key={result.studio.id}
                  result={result}
                  index={index}
                />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
