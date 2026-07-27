"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { useSearchParams } from "next/navigation";

import { useStudio } from "@entities/studio";
import { getUserFacingApiMessage } from "@shared/api";
import {
  Button,
  Card,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import { resolveConnectPhase } from "../model/resolve-connect-phase";
import { useStripeConnectActions } from "../model/use-stripe-connect-actions";
import { useStudioStripeStatus } from "../model/use-studio-stripe-status";
import { ConnectStatusSummary } from "./connect-status-summary";

export interface PayoutsPanelProps {
  studioId: number;
}

export function PayoutsPanel({ studioId }: PayoutsPanelProps) {
  const searchParams = useSearchParams();
  const autoRefreshDone = useRef(false);

  const {
    data: studio,
    isLoading: isStudioLoading,
    isError: isStudioError,
    error: studioError,
    refetch: refetchStudio,
  } = useStudio(studioId);

  const {
    data: status,
    isLoading: isStatusLoading,
    isError: isStatusError,
    error: statusError,
    refetch: refetchStatus,
  } = useStudioStripeStatus(studioId);

  const { startOnboarding, isOnboarding, refreshFromStripe, isRefreshing } =
    useStripeConnectActions({ studioId });

  const stripeReturn = searchParams.get("stripe");

  useEffect(() => {
    if (autoRefreshDone.current) return;
    if (stripeReturn !== "return" && stripeReturn !== "refresh") return;
    autoRefreshDone.current = true;
    refreshFromStripe();
  }, [refreshFromStripe, stripeReturn]);

  if (isStudioLoading || isStatusLoading) {
    return <ResourceListSkeleton testId="payouts-skeleton" rows={2} />;
  }

  if (isStudioError || !studio) {
    return (
      <ResourceErrorState
        title="Could not load studio"
        message={getUserFacingApiMessage(studioError)}
        testId="payouts-studio-error"
        onRetry={() => {
          void refetchStudio();
        }}
      />
    );
  }

  if (isStatusError || !status) {
    return (
      <ResourceErrorState
        title="Could not load payout status"
        message={getUserFacingApiMessage(statusError)}
        testId="payouts-status-error"
        onRetry={() => {
          void refetchStatus();
        }}
      />
    );
  }

  const phase = resolveConnectPhase(status);
  const onboardLabel =
    phase === "not_started" ? "Connect with Stripe" : "Continue onboarding";

  return (
    <div className="space-y-6" data-testid="payouts-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to Today
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">
          Payouts
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Stripe Connect status for {studio.name}.
        </p>
      </div>

      <Card className="space-y-5 p-6">
        <ConnectStatusSummary status={status} />

        <div className="flex flex-wrap gap-3">
          {phase !== "ready" ? (
            <Button
              type="button"
              isLoading={isOnboarding}
              disabled={isRefreshing}
              onClick={() => startOnboarding()}
              data-testid="stripe-onboard-button"
            >
              {onboardLabel}
            </Button>
          ) : null}
          <Button
            type="button"
            variant="outline"
            isLoading={isRefreshing}
            disabled={isOnboarding}
            onClick={() => refreshFromStripe()}
            data-testid="stripe-refresh-button"
          >
            Refresh from Stripe
          </Button>
        </div>
      </Card>
    </div>
  );
}
