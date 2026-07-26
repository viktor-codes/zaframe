import { describe, expect, it } from "vitest";

import {
  getSafeStripeCheckoutUrl,
  isAllowedStripeCheckoutUrl,
} from "./stripe-checkout-url";

describe("isAllowedStripeCheckoutUrl", () => {
  it("accepts checkout.stripe.com https URLs", () => {
    expect(
      isAllowedStripeCheckoutUrl("https://checkout.stripe.com/c/pay/cs_test_123"),
    ).toBe(true);
  });

  it("accepts other stripe.com subdomains over https", () => {
    expect(isAllowedStripeCheckoutUrl("https://pay.stripe.com/test")).toBe(true);
  });

  it("rejects non-https and non-Stripe hosts", () => {
    expect(
      isAllowedStripeCheckoutUrl("http://checkout.stripe.com/c/pay/cs_test"),
    ).toBe(false);
    expect(isAllowedStripeCheckoutUrl("https://evil.example/phish")).toBe(false);
    expect(
      isAllowedStripeCheckoutUrl("https://checkout.stripe.com.evil.com/x"),
    ).toBe(false);
    expect(isAllowedStripeCheckoutUrl("not-a-url")).toBe(false);
  });
});

describe("getSafeStripeCheckoutUrl", () => {
  it("returns trimmed URL or null", () => {
    expect(
      getSafeStripeCheckoutUrl("  https://checkout.stripe.com/c/pay/cs_1  "),
    ).toBe("https://checkout.stripe.com/c/pay/cs_1");
    expect(getSafeStripeCheckoutUrl("https://evil.example")).toBeNull();
    expect(getSafeStripeCheckoutUrl(null)).toBeNull();
    expect(getSafeStripeCheckoutUrl("")).toBeNull();
  });
});
