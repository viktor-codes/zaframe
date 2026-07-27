"use client";

import { useParams } from "next/navigation";

import { CheckInPanel } from "@features/check-in";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function OccurrenceCheckInPage() {
  const params = useParams();
  const studioId = parsePositiveRouteId(params.id);
  const occurrenceId = parsePositiveRouteId(params.occurrenceId);

  if (studioId == null || occurrenceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          Invalid session
        </div>
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.VIEW_BOOKINGS}
    >
      <div className="mx-auto max-w-lg px-4 py-8 sm:max-w-2xl sm:px-6 sm:py-12">
        <CheckInPanel studioId={studioId} occurrenceId={occurrenceId} />
      </div>
    </RequireStudioPermission>
  );
}
