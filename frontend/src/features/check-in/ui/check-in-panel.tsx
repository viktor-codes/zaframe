"use client";

import Link from "next/link";

import { formatOccurrenceTimeRange } from "@entities/occurrence";
import { getUserFacingApiMessage } from "@shared/api";
import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import { useAttendanceMutations } from "../model/use-attendance-mutations";
import { useOccurrenceDetail } from "../model/use-occurrence-detail";
import { useOccurrenceParticipants } from "../model/use-occurrence-participants";
import { ParticipantRow } from "./participant-row";

export interface CheckInPanelProps {
  studioId: number;
  occurrenceId: number;
}

export function CheckInPanel({ studioId, occurrenceId }: CheckInPanelProps) {
  const occurrenceQuery = useOccurrenceDetail(occurrenceId);
  const participantsQuery = useOccurrenceParticipants(occurrenceId);
  const { checkIn, markNoShow, pendingBookingId, isBusy } =
    useAttendanceMutations(studioId, occurrenceId);

  if (occurrenceQuery.isLoading || participantsQuery.isLoading) {
    return <ResourceListSkeleton testId="check-in-skeleton" rows={3} />;
  }

  if (occurrenceQuery.isError || !occurrenceQuery.data) {
    return (
      <ResourceErrorState
        title="Could not load session"
        message={getUserFacingApiMessage(occurrenceQuery.error)}
        testId="check-in-occurrence-error"
        onRetry={() => {
          void occurrenceQuery.refetch();
        }}
      />
    );
  }

  const occurrence = occurrenceQuery.data;

  if (occurrence.studio_id !== studioId) {
    return (
      <ResourceErrorState
        title="Session not in this studio"
        message="This occurrence belongs to another studio."
        testId="check-in-studio-mismatch"
        onRetry={() => {
          void occurrenceQuery.refetch();
        }}
      />
    );
  }

  if (participantsQuery.isError) {
    return (
      <ResourceErrorState
        title="Could not load participants"
        message={getUserFacingApiMessage(participantsQuery.error)}
        testId="check-in-participants-error"
        onRetry={() => {
          void participantsQuery.refetch();
        }}
      />
    );
  }

  const participants = participantsQuery.data?.items ?? [];

  return (
    <div className="space-y-6" data-testid="check-in-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to Today
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">
          {occurrence.title}
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          {formatOccurrenceTimeRange(
            occurrence.start_time,
            occurrence.end_time,
          )}
        </p>
        <p className="mt-1 text-xs text-neutral-500">
          {participants.length} participant
          {participants.length === 1 ? "" : "s"}
          {participantsQuery.data &&
          participantsQuery.data.total > participants.length
            ? ` (showing first ${participants.length} of ${participantsQuery.data.total})`
            : null}
        </p>
      </div>

      {participants.length === 0 ? (
        <ResourceEmptyState
          title="No participants yet"
          description="Confirmed bookings for this session will show up here for check-in."
          testId="check-in-empty"
        />
      ) : (
        <ul className="space-y-3">
          {participants.map((booking) => (
            <ParticipantRow
              key={booking.id}
              studioId={studioId}
              booking={booking}
              isPending={pendingBookingId === booking.id}
              isBusy={isBusy}
              onCheckIn={checkIn}
              onMarkNoShow={markNoShow}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
