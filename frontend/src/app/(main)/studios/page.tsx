import { Suspense } from "react";

import { fetchStudiosExplore } from "@shared/api/server";

import { Header } from "@features/navigation/components/Header";
import { StudiosExplore } from "@features/studios/components/studios-explore";
import { StudiosSkeleton } from "@features/studios/components/StudiosSkeleton";
import {
  parseStudiosExploreFilters,
  studiosExploreFiltersKey,
  toStudiosExploreListParams,
} from "@features/studios/model/explore-filters";

interface StudiosPageProps {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}

export default async function StudiosPage({ searchParams }: StudiosPageProps) {
  const rawParams = await searchParams;
  const filters = parseStudiosExploreFilters(rawParams);
  const listParams = toStudiosExploreListParams(filters);

  let initialPage;
  let initialFetchFailed = false;
  try {
    initialPage = await fetchStudiosExplore({
      page: 1,
      size: listParams.size ?? 12,
      is_active: listParams.is_active ?? true,
      city: listParams.city ?? undefined,
      category: listParams.category ?? undefined,
      query: listParams.query ?? undefined,
      amenities: listParams.amenities ?? undefined,
    });
  } catch {
    initialFetchFailed = true;
  }

  return (
    <Suspense fallback={<StudiosSkeleton />}>
      <StudiosExplore
        key={studiosExploreFiltersKey(filters)}
        filters={filters}
        initialPage={initialPage}
        initialFetchFailed={initialFetchFailed}
        header={
          <Header
            minimalSearch={{
              href: "#studios-search",
              placeholder: "Search studios…",
            }}
          />
        }
      />
    </Suspense>
  );
}
