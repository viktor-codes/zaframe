import type { components } from "./types.generated";

/** OpenAPI schema alias — single source of truth for API shapes. */
export type Schema<T extends keyof components["schemas"]> =
  components["schemas"][T];
