"use client";

import { useParams } from "next/navigation";

import { EditServicePanel } from "@features/manage-services";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function EditServicePage() {
  const params = useParams();
  const studioId = parsePositiveRouteId(params.id);
  const serviceId = parsePositiveRouteId(params.serviceId);

  if (studioId == null || serviceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12 text-red-800">
        Invalid service
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_SERVICES}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <EditServicePanel studioId={studioId} serviceId={serviceId} />
      </div>
    </RequireStudioPermission>
  );
}
