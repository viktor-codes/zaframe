/**
 * Defense-in-depth: only follow checkout_url values that point at Stripe.
 * Backend already returns Stripe SDK URLs; this blocks open redirects if the API is compromised.
 */

function isStripeCheckoutHostname(hostname: string): boolean {
  const host = hostname.toLowerCase();
  return host === "stripe.com" || host.endsWith(".stripe.com");
}

/** Whether `raw` is an https URL on a Stripe-controlled host. */
export function isAllowedStripeCheckoutUrl(raw: string): boolean {
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return false;
    return isStripeCheckoutHostname(url.hostname);
  } catch {
    return false;
  }
}

/**
 * Return a trimmed Stripe checkout URL, or null when unsafe/empty.
 */
export function getSafeStripeCheckoutUrl(
  raw: string | null | undefined,
): string | null {
  if (raw == null) return null;
  const trimmed = raw.trim();
  if (!trimmed) return null;
  return isAllowedStripeCheckoutUrl(trimmed) ? trimmed : null;
}
