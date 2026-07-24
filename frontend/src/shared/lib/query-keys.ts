/**
 * TanStack Query key factories — single convention for cache identity.
 *
 * Shape:
 * - list roots are plural: `studios`, `bookings`
 * - detail roots are singular: `studio`, `booking`, `occurrence`
 * - invalidate with the shortest prefix (`queryKeys.studios.all`)
 *
 * Prefer these helpers over inline string arrays.
 */

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: (loginTrigger: number) => ["auth", "me", loginTrigger] as const,
  },

  studios: {
    all: ["studios"] as const,
    explore: (params: object) => ["studios", "explore", params] as const,
    owner: (userId: number | undefined) =>
      ["studios", "owner", userId] as const,
  },

  studio: {
    detail: (id: number | undefined) => ["studio", id] as const,
    occurrences: (
      id: number,
      filters: object = {},
    ) => ["studio", id, "occurrences", filters] as const,
    services: (id: number) => ["studio", id, "services"] as const,
  },

  bookings: {
    all: ["bookings"] as const,
    my: () => ["bookings", "my"] as const,
  },

  booking: {
    detail: (id: number) => ["booking", id] as const,
  },

  occurrence: {
    detail: (id: number | undefined) => ["occurrence", id] as const,
    bookings: (id: number) => ["occurrence", id, "bookings"] as const,
  },
} as const;
