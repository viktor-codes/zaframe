"use client";

import { useParams } from "next/navigation";

import { EditServicePanel } from "@features/manage-services";
import { RequireStudioRole } from "@shared/auth";
import { StudioMemberRole } from "@shared/lib";

export default function EditServicePage() {
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
        Invalid service
      </div>
    );
  }

  return (
    <RequireStudioRole
      studioId={studioId}
      roles={[StudioMemberRole.OWNER, StudioMemberRole.MANAGER]}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <EditServicePanel studioId={studioId} serviceId={serviceId} />
      </div>
    </RequireStudioRole>
  );
}
