"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudioStripeStatus } from "@shared/api";
import { queryKeys } from "@shared/lib";

/**
 * Studio Stripe Connect status (`GET /studios/{id}/stripe/status`).
 */
export function useStudioStripeStatus(studioId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.studio.stripeStatus(studioId as number),
    queryFn: () => fetchStudioStripeStatus(studioId as number),
    enabled: studioId != null && studioId > 0,
  });
}
