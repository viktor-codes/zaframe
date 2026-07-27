import type { StripeConnectStatusResponse } from "@shared/api";

export type ConnectPhase = "not_started" | "incomplete" | "ready";

type ConnectFlags = Pick<
  StripeConnectStatusResponse,
  | "stripe_account_id"
  | "stripe_charges_enabled"
  | "stripe_payouts_enabled"
>;

/**
 * Map stored Connect flags to a dashboard phase.
 *
 * WHY: checkout requires charges_enabled; payouts need both flags (backend
 * sets completed_at only when both are true).
 */
export function resolveConnectPhase(status: ConnectFlags): ConnectPhase {
  const accountId = status.stripe_account_id?.trim() ?? "";
  if (!accountId) {
    return "not_started";
  }
  if (status.stripe_charges_enabled && status.stripe_payouts_enabled) {
    return "ready";
  }
  return "incomplete";
}

/** True when the studio can accept customer charges via Connect. */
export function isConnectChargesReady(status: ConnectFlags): boolean {
  return Boolean(
    status.stripe_account_id?.trim() && status.stripe_charges_enabled,
  );
}

/**
 * Mask a Stripe account id for display (keep prefix + last 4).
 * @example maskStripeAccountId("acct_1A2B3C4D5E") → "acct_…C4D5E" (last 4 of suffix)
 */
export function maskStripeAccountId(
  accountId: string | null | undefined,
): string | null {
  const trimmed = accountId?.trim() ?? "";
  if (!trimmed) return null;
  if (trimmed.length <= 10) return trimmed;
  return `${trimmed.slice(0, 5)}…${trimmed.slice(-4)}`;
}
