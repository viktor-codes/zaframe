"use client";

import Link from "next/link";

import {
  CapacityIndicator,
  formatOccurrenceTimeRange,
  getOccurrenceInstructorName,
  type OccurrenceResponse,
} from "@entities/occurrence";
import { PermissionGate } from "@entities/user";
import { StudioPermission } from "@shared/lib";

export interface TodaySessionCardProps {
  studioId: number;
  occurrence: OccurrenceResponse;
}

export function TodaySessionCard({
  studioId,
  occurrence,
}: TodaySessionCardProps) {
  const instructor = getOccurrenceInstructorName(occurrence);
  const confirmed = occurrence.confirmed_count ?? 0;
  const pending = occurrence.pending_count ?? 0;

  return (
    <article
      className="rounded-xl border border-neutral-200 bg-white px-4 py-3"
      data-testid={`today-session-${occurrence.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h3 className="font-display text-base font-semibold text-neutral-900">
            {occurrence.title}
          </h3>
          <p className="text-sm text-neutral-600">
            {formatOccurrenceTimeRange(
              occurrence.start_time,
              occurrence.end_time,
            )}
            {instructor ? (
              <span className="text-neutral-400"> · {instructor}</span>
            ) : null}
          </p>
          <p className="text-xs text-neutral-500">
            {confirmed} booked
            {pending > 0 ? ` · ${pending} pending` : null}
            {` · ${occurrence.max_capacity} capacity`}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <CapacityIndicator
            max_capacity={occurrence.max_capacity}
            confirmed_count={confirmed}
            pending_count={pending}
          />
          <PermissionGate
            studioId={studioId}
            permission={StudioPermission.MANAGE_SCHEDULE}
          >
            <Link
              href={`/dashboard/studios/${studioId}/calendar`}
              className="text-sm font-medium text-primary hover:text-primary-dark"
            >
              Open in calendar
            </Link>
          </PermissionGate>
        </div>
      </div>
    </article>
  );
}
