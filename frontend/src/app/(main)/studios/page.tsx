"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Search, MapPin, X } from "lucide-react";
import Link from "next/link";
import { fetchSearch } from "@/lib/api";
import type { SearchQueryParams } from "@/types/search";
import type { ServiceCategory } from "@/types/service";
import { StudioSearchCard } from "@/components/StudioSearchCard";
import { Skeleton } from "@/components/ui/Skeleton";
import { Button } from "@/components/ui/Button";

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

  useEffect(() => {
    setLocalCategory(category);
    setLocalCity(city);
  }, [category, city]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSearch(localCategory, localCity);
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2 w-full max-w-2xl">
      <div className="flex-1 flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2">
        <Search className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="Category (yoga, boxing…)"
          value={localCategory}
          onChange={(e) => setLocalCategory(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <div className="flex-1 flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2">
        <MapPin className="w-4 h-4 text-zinc-400 shrink-0" />
        <input
          type="text"
          placeholder="City"
          value={localCity}
          onChange={(e) => setLocalCity(e.target.value)}
          className="flex-1 min-w-0 bg-transparent text-sm text-zinc-900 placeholder:text-zinc-400 outline-none"
        />
      </div>
      <Button type="submit" size="md" className="shrink-0">
        Search
      </Button>
    </form>
  );
}

function StudiosSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="rounded-2xl overflow-hidden bg-white shadow-md">
          <Skeleton className="aspect-video w-full rounded-none" />
          <div className="p-4 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-6 w-20 rounded-full" />
              <Skeleton className="h-6 w-14 rounded-full" />
            </div>
            <Skeleton className="h-4 w-24 mt-2" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 px-6 text-center">
      <p className="text-2xl md:text-3xl font-bold text-zinc-800 tracking-tight">
        No vibes found in this area yet
      </p>
      <p className="text-zinc-500 mt-2 max-w-md">
        Try another city or category, or clear filters to see all studios.
      </p>
      <Button variant="secondary" className="mt-6" onClick={onReset}>
        Clear filters
      </Button>
    </div>
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
    [amenitiesParam]
  );

  const params: SearchQueryParams = useMemo(
    () => ({
      ...(category && { category: category as ServiceCategory }),
      ...(city && { city }),
      ...(query && { query }),
      ...(amenities.length > 0 && { amenities }),
    }),
    [category, city, query, amenities]
  );

  const { data: results, isLoading, isError, error } = useQuery({
    queryKey: ["search", params],
    queryFn: () => fetchSearch(params),
    staleTime: 60_000,
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
    [router, searchParams]
  );

  const resetFilters = useCallback(() => {
    router.replace("/studios", { scroll: false });
  }, [router]);

  const hasFilters = category || city || query || amenities.length > 0;

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="sticky top-0 z-40 border-b border-zinc-200 bg-white/95 backdrop-blur supports-backdrop-filter:bg-white/80">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col gap-4">
            <div className="flex items-center justify-between gap-4">
              <Link
                href="/"
                className="text-lg font-bold text-zinc-900 shrink-0"
              >
                ZeeFrame
              </Link>
              <StudiosSearchBar
                category={category}
                city={city}
                onSearch={updateSearch}
              />
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 flex flex-col lg:flex-row gap-8">
        <aside className="lg:w-64 shrink-0">
          <div className="lg:sticky lg:top-24 space-y-6">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                Category
              </h3>
              <ul className="space-y-2">
                <li>
                  <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-700 hover:text-zinc-900">
                    <input
                      type="radio"
                      name="category"
                      checked={!category}
                      onChange={() => {
                        const next = new URLSearchParams(searchParams.toString());
                        next.delete("category");
                        router.replace(`/studios?${next.toString()}`, { scroll: false });
                      }}
                      className="rounded border-zinc-300 text-teal-500 focus:ring-teal-500"
                    />
                    All
                  </label>
                </li>
                {CATEGORIES.map(({ value, label }) => (
                  <li key={value}>
                    <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-700 hover:text-zinc-900">
                      <input
                        type="radio"
                        name="category"
                        checked={category === value}
                        onChange={() => {
                          const next = new URLSearchParams(searchParams.toString());
                          next.set("category", value);
                          router.replace(`/studios?${next.toString()}`, { scroll: false });
                        }}
                        className="rounded border-zinc-300 text-teal-500 focus:ring-teal-500"
                      />
                      {label}
                    </label>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-zinc-500 mb-3">
                Amenities
              </h3>
              <ul className="space-y-2">
                {AMENITIES_OPTIONS.map((a) => {
                  const checked = amenities.includes(a);
                  return (
                    <li key={a}>
                      <label className="flex items-center gap-2 cursor-pointer text-sm text-zinc-700 hover:text-zinc-900">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => {
                            const next = new URLSearchParams(searchParams.toString());
                            const nextList = checked
                              ? amenities.filter((x) => x !== a)
                              : [...amenities, a];
                            if (nextList.length) next.set("amenities", nextList.join(","));
                            else next.delete("amenities");
                            router.replace(`/studios?${next.toString()}`, { scroll: false });
                          }}
                          className="rounded border-zinc-300 text-teal-500 focus:ring-teal-500"
                        />
                        {a.replace("_", " ")}
                      </label>
                    </li>
                  );
                })}
              </ul>
            </div>
            {hasFilters && (
              <Button variant="ghost" size="sm" onClick={resetFilters}>
                <X className="w-4 h-4 mr-1" />
                Clear filters
              </Button>
            )}
          </div>
        </aside>

        <main className="flex-1 min-w-0">
          {isError && (
            <div className="rounded-xl bg-red-50 border border-red-200 p-4 text-red-800 text-sm">
              {error instanceof Error ? error.message : "Failed to load results"}
            </div>
          )}

          {isLoading && <StudiosSkeleton />}

          {!isLoading && !isError && results && results.length === 0 && (
            <EmptyState onReset={resetFilters} />
          )}

          {!isLoading && !isError && results && results.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {results.map((result) => (
                <StudioSearchCard key={result.studio.id} result={result} />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
