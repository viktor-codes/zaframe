/**
 * Утилита для объединения имён классов (cn — classnames).
 * Поддерживает строки, объекты и условные классы.
 */
export function cn(...inputs: (string | undefined | null | false | Record<string, boolean>)[]): string {
  const classes: string[] = [];
  for (const input of inputs) {
    if (typeof input === "string" && input.trim()) {
      classes.push(input.trim());
    } else if (input && typeof input === "object" && !Array.isArray(input)) {
      for (const [key, value] of Object.entries(input)) {
        if (value && key.trim()) classes.push(key.trim());
      }
    }
  }
  return classes.join(" ");
}
