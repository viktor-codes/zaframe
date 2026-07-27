/**
 * CTA copy for OccurrenceRow when capacity / bookability is known.
 */

export function getOccurrenceBookActionLabel(options: {
  isFull: boolean;
  canBook: boolean;
  actionLabel?: string;
}): string {
  if (options.canBook) {
    return options.actionLabel ?? "Book";
  }
  return options.isFull ? "No seats left" : "Unavailable";
}
