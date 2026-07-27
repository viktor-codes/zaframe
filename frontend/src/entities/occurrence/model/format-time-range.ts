/**
 * Local wall-clock time range for occurrence cards (browser timezone).
 * Shared by Today and Calendar — keep one formatter to avoid en-IE drift.
 */
export function formatOccurrenceTimeRange(
  startIso: string,
  endIso: string,
  locale = "en-IE",
): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const opts: Intl.DateTimeFormatOptions = {
    hour: "2-digit",
    minute: "2-digit",
  };
  return `${start.toLocaleTimeString(locale, opts)} – ${end.toLocaleTimeString(locale, opts)}`;
}
