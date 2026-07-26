"use client";

import { useParams } from "next/navigation";

import { ScheduleTemplatesPanel } from "@features/manage-schedule";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

export default function ServiceSchedulePage() {
  const params = useParams();
  const studioId = Number(params.id);
  const serviceId = Number(params.serviceId);

  if (
    !Number.isFinite(studioId) ||
    studioId <= 0 ||
    !Number.isFinite(serviceId) ||
    serviceId <= 0
  ) {
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
