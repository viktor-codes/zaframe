import type { QueryClient } from "@tanstack/react-query";

import { queryKeys } from "@shared/lib";

/**
 * Invalidate every cached occurrences list for a studio (Today, Calendar, …).
 */
export function invalidateStudioOccurrences(
  queryClient: QueryClient,
  studioId: number,
): void {
  void queryClient.invalidateQueries({
    queryKey: queryKeys.studio.occurrencesRoot(studioId),
  });
}

/**
 * Invalidate every cached services list for a studio (CRUD + onboarding).
 */
export function invalidateStudioServices(
  queryClient: QueryClient,
  studioId: number,
): void {
  void queryClient.invalidateQueries({
    queryKey: queryKeys.studio.servicesRoot(studioId),
  });
}

/**
 * Invalidate the studio members list (`GET /studios/{id}/members`).
 */
export function invalidateStudioMembers(
  queryClient: QueryClient,
  studioId: number,
): void {
  void queryClient.invalidateQueries({
    queryKey: queryKeys.studio.membersRoot(studioId),
  });
}
