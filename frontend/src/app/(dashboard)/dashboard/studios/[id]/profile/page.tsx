"use client";

import { useParams } from "next/navigation";

import { EditStudioPanel } from "@features/manage-studio";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function StudioProfilePage() {
  const params = useParams();
  const studioId = parsePositiveRouteId(params.id);

  if (studioId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          Invalid studio
        </div>
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_STUDIO}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <EditStudioPanel studioId={studioId} />
      </div>
    </RequireStudioPermission>
  );
}
