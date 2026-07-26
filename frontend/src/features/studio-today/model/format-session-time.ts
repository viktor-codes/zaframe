/** Local time range for a Today session card (browser local). */
export function formatSessionTimeRange(
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
