"use client";

import { useParams } from "next/navigation";

import { StudioCalendarPanel } from "@features/manage-schedule";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function StudioCalendarPage() {
  const params = useParams();
  const studioId = parsePositiveRouteId(params.id);

  if (studioId == null) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 text-red-800">
        Invalid studio
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_SCHEDULE}
    >
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-12">
        <StudioCalendarPanel studioId={studioId} />
      </div>
    </RequireStudioPermission>
  );
}
