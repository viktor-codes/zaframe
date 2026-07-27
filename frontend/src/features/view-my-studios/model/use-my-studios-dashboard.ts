"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import { studioServicesQueryOptions } from "@entities/service";
import {
  pickSpotlightStudioStep,
  resolveStudioOnboardingStep,
  useMyStudios,
  type StudioOnboardingStep,
  type StudioWithRoleResponse,
} from "@entities/studio";
import { fetchStudioStripeStatus } from "@shared/api";
import { queryKeys, roleHasPermission, StudioPermission } from "@shared/lib";

import {
  buildConnectByStudioId,
  buildServicesByStudioId,
  findRoleScopedQueryIssue,
} from "./onboarding-query-maps";

export interface StudioListRow {
  studio: StudioWithRoleResponse;
  step: StudioOnboardingStep | null;
}

export interface UseMyStudiosDashboardResult {
  rows: StudioListRow[];
  spotlight: {
    studio: StudioWithRoleResponse;
    step: StudioOnboardingStep;
  } | null;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
}

export function useMyStudiosDashboard(): UseMyStudiosDashboardResult {
  const myStudiosQuery = useMyStudios();
  const studios = myStudiosQuery.data?.items ?? [];

  // WHY: onboarding only needs visibility presence; one larger page is enough
  // for funnel steps. Full CRUD lists use infinite query elsewhere.
  const onboardingServicesParams = { size: 100 } as const;

  const serviceQueries = useQueries({
    queries: studios.map((studio) => ({
      ...studioServicesQueryOptions(studio.id, onboardingServicesParams),
      enabled:
        myStudiosQuery.isSuccess &&
        roleHasPermission(studio.role, StudioPermission.MANAGE_SERVICES),
    })),
  });

  const connectQueries = useQueries({
    queries: studios.map((studio) => ({
      queryKey: queryKeys.studio.stripeStatus(studio.id),
      queryFn: () => fetchStudioStripeStatus(studio.id),
      enabled:
        myStudiosQuery.isSuccess &&
        roleHasPermission(studio.role, StudioPermission.MANAGE_PAYOUTS),
    })),
  });

  const servicesByStudioId = useMemo(
    () => buildServicesByStudioId(studios, serviceQueries),
    [serviceQueries, studios],
  );

  const connectByStudioId = useMemo(
    () => buildConnectByStudioId(studios, connectQueries),
    [connectQueries, studios],
  );

  const rows = useMemo<StudioListRow[]>(
    () =>
      studios.map((studio) => ({
        studio,
        step: resolveStudioOnboardingStep(
          studio,
          servicesByStudioId.get(studio.id),
          connectByStudioId.get(studio.id),
        ),
      })),
    [connectByStudioId, servicesByStudioId, studios],
  );

  const spotlight = useMemo(() => {
    const picked = pickSpotlightStudioStep(
      studios,
      servicesByStudioId,
      connectByStudioId,
    );
    if (picked == null) {
      return null;
    }
    return {
      studio: picked.studio as StudioWithRoleResponse,
      step: picked.step,
    };
  }, [connectByStudioId, servicesByStudioId, studios]);

  const servicesIssue = findRoleScopedQueryIssue(
    studios,
    serviceQueries,
    StudioPermission.MANAGE_SERVICES,
  );
  const connectIssue = findRoleScopedQueryIssue(
    studios,
    connectQueries,
    StudioPermission.MANAGE_PAYOUTS,
  );

  return {
    rows,
    spotlight,
    isLoading:
      myStudiosQuery.isLoading ||
      servicesIssue.isLoading ||
      connectIssue.isLoading,
    isError:
      myStudiosQuery.isError ||
      Boolean(servicesIssue.failed) ||
      Boolean(connectIssue.failed),
    error:
      myStudiosQuery.error ??
      servicesIssue.failed?.error ??
      connectIssue.failed?.error,
    refetch: () => {
      void myStudiosQuery.refetch();
      for (const query of serviceQueries) {
        void query.refetch();
      }
      for (const query of connectQueries) {
        void query.refetch();
      }
    },
  };
}
