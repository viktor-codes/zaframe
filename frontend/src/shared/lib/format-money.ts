/**
 * Display money amounts in EUR (product currency for ZeeFrame MVP).
 */

const EUR_FROM_CENTS = new Intl.NumberFormat("en-IE", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Format an integer cent amount as a EUR string (e.g. 1500 → "€15.00").
 */
export function formatMoneyFromCents(cents: number): string {
  return EUR_FROM_CENTS.format(cents / 100);
}
