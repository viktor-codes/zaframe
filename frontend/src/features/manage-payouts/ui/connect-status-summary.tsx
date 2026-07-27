"use client";

import type { StripeConnectStatusResponse } from "@shared/api";

import {
  maskStripeAccountId,
  resolveConnectPhase,
  type ConnectPhase,
} from "../model/resolve-connect-phase";

export interface ConnectStatusSummaryProps {
  status: StripeConnectStatusResponse;
}

const PHASE_COPY: Record<
  ConnectPhase,
  { title: string; description: string; badgeClass: string; badgeLabel: string }
> = {
  not_started: {
    title: "Connect Stripe to get paid",
    description:
      "Customers can browse your classes, but paid bookings stay blocked until Stripe Connect is ready.",
    badgeClass: "bg-amber-50 text-amber-900",
    badgeLabel: "Not connected",
  },
  incomplete: {
    title: "Finish Stripe onboarding",
    description:
      "Your Stripe account is linked, but charges or payouts are still disabled. Continue onboarding to accept payments.",
    badgeClass: "bg-amber-50 text-amber-900",
    badgeLabel: "Action needed",
  },
  ready: {
    title: "Stripe Connect is ready",
    description:
      "Charges and payouts are enabled. New paid bookings can settle to this studio.",
    badgeClass: "bg-teal-50 text-teal-900",
    badgeLabel: "Ready",
  },
};

function FlagRow({ label, isEnabled }: { label: string; isEnabled: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 text-sm">
      <span className="text-neutral-600">{label}</span>
      <span
        className={
          isEnabled
            ? "font-medium text-teal-800"
            : "font-medium text-neutral-500"
        }
      >
        {isEnabled ? "Enabled" : "Disabled"}
      </span>
    </div>
  );
}

export function ConnectStatusSummary({ status }: ConnectStatusSummaryProps) {
  const phase = resolveConnectPhase(status);
  const copy = PHASE_COPY[phase];
  const maskedAccount = maskStripeAccountId(status.stripe_account_id);

  return (
    <div className="space-y-4" data-testid="connect-status-summary">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-secondary font-display text-xl font-bold">
            {copy.title}
          </h2>
          <p className="mt-1 text-sm text-neutral-600">{copy.description}</p>
        </div>
        <span
          className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${copy.badgeClass}`}
          data-testid="connect-phase-badge"
        >
          {copy.badgeLabel}
        </span>
      </div>

      <div className="space-y-2 rounded-lg border border-neutral-200 bg-neutral-50 p-4">
        <FlagRow
          label="Accept charges"
          isEnabled={status.stripe_charges_enabled}
        />
        <FlagRow
          label="Receive payouts"
          isEnabled={status.stripe_payouts_enabled}
        />
        {maskedAccount ? (
          <div className="flex items-center justify-between gap-3 border-t border-neutral-200 pt-2 text-sm">
            <span className="text-neutral-600">Stripe account</span>
            <span
              className="font-mono text-neutral-800"
              data-testid="stripe-account-id"
            >
              {maskedAccount}
            </span>
          </div>
        ) : null}
        {status.stripe_onboarding_completed_at ? (
          <p className="border-t border-neutral-200 pt-2 text-xs text-neutral-500">
            Completed{" "}
            {new Date(status.stripe_onboarding_completed_at).toLocaleString()}
          </p>
        ) : null}
      </div>
    </div>
  );
}
