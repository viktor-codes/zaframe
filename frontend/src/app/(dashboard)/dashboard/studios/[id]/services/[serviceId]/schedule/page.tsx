"use client";

import { useParams } from "next/navigation";

import { ScheduleTemplatesPanel } from "@features/manage-schedule";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function ServiceSchedulePage() {
  const params = useParams();
  const studioId = parsePositiveRouteId(params.id);
  const serviceId = parsePositiveRouteId(params.serviceId);

  if (studioId == null || serviceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12 text-red-800">
        Invalid schedule route
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_SCHEDULE}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <ScheduleTemplatesPanel studioId={studioId} serviceId={serviceId} />
      </div>
    </RequireStudioPermission>
  );
}
