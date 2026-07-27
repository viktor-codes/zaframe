"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createStudioStripeOnboarding,
  updateStudioPayoutSettings,
} from "@shared/api";
import { getSafeStripeCheckoutUrl, queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

export interface UseStripeConnectActionsOptions {
  studioId: number;
  /** Navigate to Stripe-hosted onboarding (injected for testability). */
  redirectTo?: (url: string) => void;
}

/**
 * Onboard + refresh mutations for the payouts dashboard.
 */
export function useStripeConnectActions({
  studioId,
  redirectTo = (url) => {
    window.location.assign(url);
  },
}: UseStripeConnectActionsOptions) {
  const queryClient = useQueryClient();

  const invalidateStatus = () => {
    void queryClient.invalidateQueries({
      queryKey: queryKeys.studio.stripeStatus(studioId),
    });
  };

  const onboardMutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: async () => {
      const origin = window.location.origin;
      const payoutsUrl = `${origin}/dashboard/studios/${studioId}/payouts`;
      return createStudioStripeOnboarding(studioId, {
        return_url: `${payoutsUrl}?stripe=return`,
        refresh_url: `${payoutsUrl}?stripe=refresh`,
      });
    },
    onSuccess: (result) => {
      invalidateStatus();
      const safeUrl = getSafeStripeCheckoutUrl(result.onboarding_url);
      if (!safeUrl) {
        toast.error("Could not open Stripe onboarding. Please try again.");
        return;
      }
      redirectTo(safeUrl);
    },
  });

  const refreshMutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: () =>
      updateStudioPayoutSettings(studioId, { refresh_from_stripe: true }),
    onSuccess: (status) => {
      queryClient.setQueryData(
        queryKeys.studio.stripeStatus(studioId),
        status,
      );
      toast.success("Payout status updated from Stripe");
    },
  });

  return {
    startOnboarding: onboardMutation.mutate,
    isOnboarding: onboardMutation.isPending,
    refreshFromStripe: refreshMutation.mutate,
    isRefreshing: refreshMutation.isPending,
  };
}
