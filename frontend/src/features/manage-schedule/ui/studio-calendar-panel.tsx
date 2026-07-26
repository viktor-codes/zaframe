"use client";

import Link from "next/link";

import { getUserFacingApiMessage } from "@shared/api";
import {
  Button,
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
  Tabs,
} from "@shared/ui";

import {
  CALENDAR_DEFAULT_WEEKS,
  type CalendarStatusFilter,
} from "../model/calendar-range";
import { useStudioCalendar } from "../model/use-studio-calendar";
import { CalendarDayGroup } from "./calendar-day-group";

export interface StudioCalendarPanelProps {
  studioId: number;
}

const STATUS_TABS: { id: CalendarStatusFilter; label: string }[] = [
  { id: "scheduled", label: "Scheduled" },
  { id: "cancelled", label: "Cancelled" },
  { id: "completed", label: "Completed" },
  { id: "all", label: "All" },
];

export function StudioCalendarPanel({ studioId }: StudioCalendarPanelProps) {
  const {
    statusFilter,
    setStatusFilter,
    groups,
    totalCount,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useStudioCalendar(studioId);

  if (isLoading) {
    return <ResourceListSkeleton testId="calendar-skeleton" rows={4} />;
  }

  if (isError) {
    return (
      <ResourceErrorState
        title="Could not load calendar"
        message={getUserFacingApiMessage(error)}
        testId="calendar-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="studio-calendar-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-secondary font-display text-2xl font-bold">
            Calendar
          </h1>
          <p className="mt-1 text-sm text-neutral-600">
            Sessions for the next {CALENDAR_DEFAULT_WEEKS} weeks, grouped by
            date. Edit or cancel concrete sessions here — template changes never
            rewrite this list.
          </p>
        </div>
        <Link
          href={`/dashboard/studios/${studioId}/services`}
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          Manage templates →
        </Link>
      </div>

      <Tabs
        tabs={STATUS_TABS}
        activeTab={statusFilter}
        onChange={(id) => setStatusFilter(id as CalendarStatusFilter)}
      />

      {totalCount === 0 ? (
        <ResourceEmptyState
          title={
            statusFilter === "scheduled"
              ? "No scheduled sessions"
              : "No sessions in this view"
          }
          description="Generate sessions from a service schedule template, or switch filters."
          testId="calendar-empty"
          ctaHref={`/dashboard/studios/${studioId}/services`}
          ctaLabel="Go to services"
        />
      ) : (
        <div className="space-y-8">
          {groups.map((group) => (
            <CalendarDayGroup
              key={group.dateKey}
              studioId={studioId}
              group={group}
            />
          ))}
        </div>
      )}

      {hasNextPage ? (
        <div className="flex justify-center">
          <Button
            type="button"
            variant="secondary"
            isLoading={isFetchingNextPage}
            onClick={() => {
              void fetchNextPage();
            }}
            data-testid="calendar-load-more"
          >
            Load more
          </Button>
        </div>
      ) : null}
    </div>
  );
}
