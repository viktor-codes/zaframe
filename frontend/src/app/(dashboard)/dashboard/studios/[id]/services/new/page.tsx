"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { CreateServiceForm } from "@features/manage-services";
import { RequireStudioRole } from "@shared/auth";
import { StudioMemberRole } from "@shared/lib";
import { Card } from "@shared/ui";

export default function NewServicePage() {
  const params = useParams();
  const studioId = Number(params.id);

  if (!Number.isFinite(studioId) || studioId <= 0) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12 text-red-800">
        Invalid studio
      </div>
    );
  }

  return (
    <RequireStudioRole
      studioId={studioId}
      roles={[StudioMemberRole.OWNER, StudioMemberRole.MANAGER]}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <Link
          href={`/dashboard/studios/${studioId}/services`}
          className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to services
        </Link>
        <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
          Create service
        </h1>
        <p className="mb-6 text-sm text-neutral-600">
          Starts as a draft. Publish when you are ready for bookings.
        </p>
        <Card className="p-6">
          <CreateServiceForm studioId={studioId} />
        </Card>
      </div>
    </RequireStudioRole>
  );
}
