/** Convert API ISO instant → `datetime-local` input value (browser local). */
export function toDatetimeLocalValue(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

/** Convert `datetime-local` value → UTC ISO for the API. */
export function fromDatetimeLocalValue(localValue: string): string {
  return new Date(localValue).toISOString();
}

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
