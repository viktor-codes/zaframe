"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import {
  pickSpotlightStudioStep,
  resolveStudioOnboardingStep,
  useMyStudios,
  type StudioOnboardingStep,
  type StudioWithRoleResponse,
} from "@entities/studio";
import { fetchStudioServices } from "@shared/api";
import {
  queryKeys,
  roleHasPermission,
  StudioPermission,
} from "@shared/lib";

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
    queries: studios.map((studio) => {
      const canManageServices = roleHasPermission(
        studio.role,
        StudioPermission.MANAGE_SERVICES,
      );

      return {
        queryKey: queryKeys.studio.services(
          studio.id,
          onboardingServicesParams,
        ),
        queryFn: () =>
          fetchStudioServices(studio.id, onboardingServicesParams),
        enabled: myStudiosQuery.isSuccess && canManageServices,
      };
    }),
  });

  const servicesByStudioId = useMemo(() => {
    const map = new Map<
      number,
      ReadonlyArray<{ visibility: string }> | undefined
    >();

    studios.forEach((studio, index) => {
      const canManageServices = roleHasPermission(
        studio.role,
        StudioPermission.MANAGE_SERVICES,
      );

      if (!canManageServices) {
        map.set(studio.id, undefined);
        return;
      }

      const query = serviceQueries[index];
      if (!query || query.isLoading || query.isPending) {
        map.set(studio.id, undefined);
        return;
      }

      if (query.isError) {
        // Fail soft: treat as empty so the owner still gets a create-service CTA.
        map.set(studio.id, []);
        return;
      }

      map.set(studio.id, query.data?.items ?? []);
    });

    return map;
  }, [serviceQueries, studios]);

  const rows = useMemo<StudioListRow[]>(
    () =>
      studios.map((studio) => ({
        studio,
        step: resolveStudioOnboardingStep(
          studio,
          servicesByStudioId.get(studio.id),
        ),
      })),
    [servicesByStudioId, studios],
  );

  const spotlight = useMemo(() => {
    const picked = pickSpotlightStudioStep(studios, servicesByStudioId);
    if (picked == null) {
      return null;
    }
    return {
      studio: picked.studio as StudioWithRoleResponse,
      step: picked.step,
    };
  }, [servicesByStudioId, studios]);

  const isServicesLoading = serviceQueries.some(
    (query, index) =>
      roleHasPermission(studios[index]?.role, StudioPermission.MANAGE_SERVICES) &&
      (query.isLoading || query.isPending),
  );

  return {
    rows,
    spotlight,
    isLoading: myStudiosQuery.isLoading || isServicesLoading,
    isError: myStudiosQuery.isError,
    error: myStudiosQuery.error,
    refetch: () => {
      void myStudiosQuery.refetch();
    },
  };
}
