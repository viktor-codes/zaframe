/**
 * TanStack Query key factories — single convention for cache identity.
 *
 * Shape:
 * - list roots are plural: `studios`, `bookings`
 * - detail roots are singular: `studio`, `booking`, `occurrence`
 * - invalidate with the shortest prefix (`queryKeys.studios.all`)
 *
 * WHY: `filters` / list `params` in the key must match the object passed to the
 * fetch function — otherwise cache hits can serve the wrong payload.
 */

import type { BookingsListParams, MyBookingsParams } from "../api/bookings";
import type { MyOrdersParams } from "../api/orders";
import type {
  StudioOccurrencesParams,
  StudioServicesParams,
  StudiosListParams,
} from "../api/studios";

export type {
  BookingsListParams,
  MyBookingsParams,
  MyOrdersParams,
  StudioOccurrencesParams,
  StudioServicesParams,
  StudiosListParams,
};

export const queryKeys = {
  auth: {
    all: ["auth"] as const,
    me: (loginTrigger: number) => ["auth", "me", loginTrigger] as const,
  },

  studios: {
    all: ["studios"] as const,
    explore: (params: StudiosListParams) =>
      ["studios", "explore", params] as const,
    /** Membership list for the authenticated user (`GET /studios/my`). */
    my: ["studios", "my"] as const,
    owner: (userId: number | undefined) =>
      ["studios", "owner", userId] as const,
  },

  studio: {
    detail: (id: number | undefined) => ["studio", id] as const,
    /**
     * @param filters - Exact params passed to `fetchStudioOccurrences` (no silent defaults in the key).
     */
    occurrences: (id: number, filters: StudioOccurrencesParams) =>
      ["studio", id, "occurrences", filters] as const,
    /**
     * Studio dashboard bookings (`GET /bookings?studio_id=…`).
     * @param filters - Exact params passed to `fetchBookings` (must include `studio_id`).
     */
    bookings: (id: number, filters: BookingsListParams) =>
      ["studio", id, "bookings", filters] as const,
    publicServiceOccurrences: (slug: string, serviceId: number) =>
      ["studio", "slug", slug, "service", serviceId, "occurrences"] as const,
    /** Prefix for invalidating every services list for a studio. */
    servicesRoot: (id: number) => ["studio", id, "services"] as const,
    /**
     * @param filters - Exact params passed to `fetchStudioServices` (no `page`;
     *   infinite query supplies page via pageParam).
     */
    services: (
      id: number,
      filters: Omit<StudioServicesParams, "page"> = {},
    ) => ["studio", id, "services", filters] as const,
  },

  service: {
    detail: (id: number | undefined) => ["service", id] as const,
    scheduleTemplates: (serviceId: number) =>
      ["service", serviceId, "schedule-templates"] as const,
  },

  bookings: {
    all: ["bookings"] as const,
    /**
     * @param params - Exact list filters passed to `fetchMyBookings` (no `page`;
     *   infinite query supplies page via pageParam).
     */
    my: (params: Omit<MyBookingsParams, "page"> = {}) =>
      ["bookings", "my", params] as const,
  },

  booking: {
    detail: (id: number) => ["booking", id] as const,
  },

  orders: {
    all: ["orders"] as const,
    /**
     * @param params - Exact list filters passed to `fetchMyOrders` (no `page`).
     */
    my: (params: Omit<MyOrdersParams, "page"> = {}) =>
      ["orders", "my", params] as const,
  },

  occurrence: {
    detail: (id: number | undefined) => ["occurrence", id] as const,
    bookings: (id: number) => ["occurrence", id, "bookings"] as const,
  },
} as const;
