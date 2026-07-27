/**
 * WHY: `disabled ?? isLoading` is wrong when the caller passes `disabled={false}`
 * (e.g. `disabled={isOccurrenceFull}` while the seat is free) — `??` keeps `false`
 * and the button stays clickable during loading, enabling double-submit.
 */
export function resolveButtonDisabled(
  disabled: boolean | undefined,
  isLoading: boolean,
): boolean {
  return Boolean(disabled) || isLoading;
}
