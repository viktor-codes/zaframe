"use client";

import { useParams } from "next/navigation";

import { EditStudioPanel } from "@features/manage-studio";
import { RequireStudioRole } from "@shared/auth";
import { StudioMemberRole } from "@shared/lib";

export default function StudioProfilePage() {
  const params = useParams();
  const studioId = Number(params.id);

  if (!Number.isFinite(studioId) || studioId <= 0) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          Invalid studio
        </div>
      </div>
    );
  }

  return (
    <RequireStudioRole
      studioId={studioId}
      roles={[StudioMemberRole.OWNER]}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <EditStudioPanel studioId={studioId} />
      </div>
    </RequireStudioRole>
  );
}
