"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";

import { PayoutsPanel } from "@features/manage-payouts";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib";
import { ResourceListSkeleton } from "@shared/ui";

import { parsePositiveRouteId } from "@/app/(dashboard)/parse-route-id";

export default function StudioPayoutsPage() {
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
      permission={StudioPermission.MANAGE_PAYOUTS}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <Suspense
          fallback={<ResourceListSkeleton testId="payouts-skeleton" rows={2} />}
        >
          <PayoutsPanel studioId={studioId} />
        </Suspense>
      </div>
    </RequireStudioPermission>
  );
}
