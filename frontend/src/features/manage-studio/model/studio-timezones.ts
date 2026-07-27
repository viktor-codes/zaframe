/** Common IANA zones for browsers without `Intl.supportedValuesOf`. */
const FALLBACK_TIMEZONES = [
  "UTC",
  "Europe/Dublin",
  "Europe/London",
  "Europe/Berlin",
  "Europe/Paris",
  "America/New_York",
  "America/Los_Angeles",
  "Asia/Tokyo",
] as const;

export function listStudioTimezones(): string[] {
  const supported =
    typeof Intl !== "undefined" && "supportedValuesOf" in Intl
      ? Intl.supportedValuesOf("timeZone")
      : [...FALLBACK_TIMEZONES];

  return supported;
}

export function defaultStudioTimezone(): string {
  return Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Dublin";
}
