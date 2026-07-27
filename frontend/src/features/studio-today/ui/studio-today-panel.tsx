"use client";

import { getUserFacingApiMessage } from "@shared/api";
import { usePermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";
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
  const { can } = usePermission(studioId);
  const canManageSchedule = can(StudioPermission.MANAGE_SCHEDULE);
  const canViewBookings = can(StudioPermission.VIEW_BOOKINGS);

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

  let emptyDescription =
    "No sessions on the board today. Check back when the schedule is published.";
  let emptyCtaHref: string | undefined;
  let emptyCtaLabel: string | undefined;

  if (canManageSchedule) {
    emptyDescription =
      "Generate sessions from a schedule template, or open the calendar to plan ahead.";
    emptyCtaHref = `/dashboard/studios/${studioId}/calendar`;
    emptyCtaLabel = "Open calendar";
  } else if (canViewBookings) {
    emptyDescription =
      "No sessions on the board today. Check bookings for upcoming participants.";
    emptyCtaHref = `/dashboard/studios/${studioId}/bookings`;
    emptyCtaLabel = "View bookings";
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
          description={emptyDescription}
          testId="today-empty"
          ctaHref={emptyCtaHref}
          ctaLabel={emptyCtaLabel}
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
