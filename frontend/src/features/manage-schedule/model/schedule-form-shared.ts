export const TIME_RE = /^([01]\d|2[0-3]):([0-5]\d)(?::([0-5]\d))?$/;
export const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function normalizeStartTime(value: string): string {
  const match = TIME_RE.exec(value.trim());
  if (!match) return value.trim();
  return `${match[1]}:${match[2]}:00`;
}
