import { describe, expect, it } from "vitest";

import {
  isConnectChargesReady,
  maskStripeAccountId,
  resolveConnectPhase,
} from "./resolve-connect-phase";

const base = {
  stripe_account_id: null as string | null,
  stripe_charges_enabled: false,
  stripe_payouts_enabled: false,
};

describe("resolveConnectPhase", () => {
  it("returns not_started when there is no account", () => {
    expect(resolveConnectPhase(base)).toBe("not_started");
    expect(resolveConnectPhase({ ...base, stripe_account_id: "  " })).toBe(
      "not_started",
    );
  });

  it("returns incomplete when an account exists but flags are off", () => {
    expect(
      resolveConnectPhase({
        ...base,
        stripe_account_id: "acct_1",
        stripe_charges_enabled: true,
        stripe_payouts_enabled: false,
      }),
    ).toBe("incomplete");
  });

  it("returns ready only when charges and payouts are enabled", () => {
    expect(
      resolveConnectPhase({
        ...base,
        stripe_account_id: "acct_1",
        stripe_charges_enabled: true,
        stripe_payouts_enabled: true,
      }),
    ).toBe("ready");
  });
});

describe("isConnectChargesReady", () => {
  it("requires account id and charges_enabled", () => {
    expect(isConnectChargesReady(base)).toBe(false);
    expect(
      isConnectChargesReady({
        ...base,
        stripe_account_id: "acct_1",
        stripe_charges_enabled: true,
      }),
    ).toBe(true);
  });
});

describe("maskStripeAccountId", () => {
  it("masks long account ids and leaves short ones intact", () => {
    expect(maskStripeAccountId(null)).toBeNull();
    expect(maskStripeAccountId("acct_short")).toBe("acct_short");
    expect(maskStripeAccountId("acct_1A2B3C4D5E6F")).toBe("acct_…5E6F");
  });
});
