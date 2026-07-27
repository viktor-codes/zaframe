"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { fetchService, getUserFacingApiMessage } from "@shared/api";
import { queryKeys } from "@shared/lib";
import {
  Card,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import { EditServiceForm } from "./edit-service-form";

export interface EditServicePanelProps {
  studioId: number;
  serviceId: number;
}

export function EditServicePanel({
  studioId,
  serviceId,
}: EditServicePanelProps) {
  const {
    data: service,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.service.detail(serviceId),
    queryFn: () => fetchService(serviceId),
  });

  if (isLoading) {
    return <ResourceListSkeleton testId="edit-service-skeleton" rows={2} />;
  }

  if (isError || !service) {
    return (
      <ResourceErrorState
        title="Could not load service"
        message={getUserFacingApiMessage(error)}
        testId="edit-service-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  if (service.studio_id !== studioId) {
    return (
      <ResourceErrorState
        title="Service not in this studio"
        message="This service belongs to a different studio."
        testId="edit-service-wrong-studio"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="edit-service-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}/services`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to services
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">
          {service.name}
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Edit details or change storefront visibility.
        </p>
      </div>
      <Card className="p-6">
        <EditServiceForm studioId={studioId} service={service} />
      </Card>
    </div>
  );
}
