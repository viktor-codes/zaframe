"use client";

import Link from "next/link";

import { getUserFacingApiMessage } from "@shared/api";
import { ServiceVisibility } from "@shared/lib";
import {
  Button,
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
  Tabs,
} from "@shared/ui";

import {
  useStudioServices,
  type ServiceVisibilityTab,
} from "../model/use-studio-services";
import { ServiceListCard } from "./service-list-card";

export interface ServicesPanelProps {
  studioId: number;
}

export function ServicesPanel({ studioId }: ServicesPanelProps) {
  const {
    activeTab,
    setActiveTab,
    counts,
    tabServices,
    totalCount,
    isLoading,
    isError,
    error,
    refetch,
  } = useStudioServices(studioId);

  if (isLoading) {
    return <ResourceListSkeleton testId="services-skeleton" rows={3} />;
  }

  if (isError) {
    return (
      <ResourceErrorState
        title="Could not load services"
        message={getUserFacingApiMessage(error)}
        testId="services-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  const tabs = [
    {
      id: ServiceVisibility.DRAFT,
      label: `Draft (${counts.draft})`,
    },
    {
      id: ServiceVisibility.PUBLISHED,
      label: `Published (${counts.published})`,
    },
    {
      id: ServiceVisibility.ARCHIVED,
      label: `Archived (${counts.archived})`,
    },
  ];

  return (
    <div className="space-y-6" data-testid="services-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-secondary font-display text-2xl font-bold">
            Services
          </h1>
          <p className="mt-1 text-sm text-neutral-600">
            Draft, publish, and archive offerings for this studio.
          </p>
        </div>
        <Button asChild>
          <Link href={`/dashboard/studios/${studioId}/services/new`}>
            Add service
          </Link>
        </Button>
      </div>

      {totalCount === 0 ? (
        <ResourceEmptyState
          title="No services yet"
          description="Create a draft class or course, then publish it to the storefront."
          testId="services-empty"
          ctaHref={`/dashboard/studios/${studioId}/services/new`}
          ctaLabel="Create service"
        />
      ) : (
        <>
          <Tabs
            tabs={tabs}
            activeTab={activeTab}
            onChange={(id) => setActiveTab(id as ServiceVisibilityTab)}
          />

          {tabServices.length === 0 ? (
            <ResourceEmptyState
              title={`No ${activeTab} services`}
              description="Switch tabs or create a new draft service."
              testId="services-tab-empty"
            />
          ) : (
            <div className="grid gap-3">
              {tabServices.map((service) => (
                <ServiceListCard
                  key={service.id}
                  studioId={studioId}
                  service={service}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
