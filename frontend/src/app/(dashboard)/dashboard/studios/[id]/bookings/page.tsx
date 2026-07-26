"use client";

import { useParams } from "next/navigation";

import { StudioBookingsPanel } from "@features/view-studio-bookings";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

export default function StudioBookingsPage() {
  const params = useParams();
  const studioId = Number(params.id);

  if (!Number.isFinite(studioId) || studioId <= 0) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 text-red-800">
        Invalid studio
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.VIEW_BOOKINGS}
    >
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-12">
        <StudioBookingsPanel studioId={studioId} />
      </div>
    </RequireStudioPermission>
  );
}
