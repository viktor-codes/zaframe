"use client";

import { useParams } from "next/navigation";

import { StudioCalendarPanel } from "@features/manage-schedule";
import { RequireStudioRole } from "@shared/auth";
import { StudioMemberRole } from "@shared/lib";

export default function StudioCalendarPage() {
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
    <RequireStudioRole
      studioId={studioId}
      roles={[StudioMemberRole.OWNER, StudioMemberRole.MANAGER]}
    >
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-12">
        <StudioCalendarPanel studioId={studioId} />
      </div>
    </RequireStudioRole>
  );
}
