"use client";

import { getUserFacingApiMessage } from "@shared/api";
import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import { useStudioToday } from "../model/use-studio-today";
import { TodayCounters } from "./today-counters";
import { TodayQuickActions } from "./today-quick-actions";
import { TodaySessionCard } from "./today-session-card";

export interface StudioTodayPanelProps {
  studioId: number;
}

export function StudioTodayPanel({ studioId }: StudioTodayPanelProps) {
  const {
    heading,
    sessions,
    summary,
    isLoading,
    isError,
    error,
    refetch,
  } = useStudioToday(studioId);

  if (isLoading) {
    return <ResourceListSkeleton testId="today-skeleton" rows={3} />;
  }

  if (isError) {
    return (
      <ResourceErrorState
        title="Could not load today's sessions"
        message={getUserFacingApiMessage(error)}
        testId="today-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="studio-today-panel">
      <div>
        <h1 className="text-secondary font-display text-2xl font-bold">
          Today
        </h1>
        <p className="mt-1 text-sm text-neutral-600">{heading}</p>
      </div>

      <TodayCounters summary={summary} />
      <TodayQuickActions studioId={studioId} />

      {sessions.length === 0 ? (
        <ResourceEmptyState
          title="No sessions today"
          description="Generate sessions from a schedule template, or open the calendar to plan ahead."
          testId="today-empty"
          ctaHref={`/dashboard/studios/${studioId}/calendar`}
          ctaLabel="Open calendar"
        />
      ) : (
        <section className="space-y-3" aria-label="Today's sessions">
          <h2 className="text-sm font-semibold tracking-wide text-neutral-500 uppercase">
            Sessions
          </h2>
          <div className="grid gap-3">
            {sessions.map((occurrence) => (
              <TodaySessionCard
                key={occurrence.id}
                studioId={studioId}
                occurrence={occurrence}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
