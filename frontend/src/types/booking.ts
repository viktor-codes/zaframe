/**
 * Booking types aligned with backend schemas.
 */

import type { OccurrenceResponse } from "./occurrence";
import type { StudioResponse } from "./studio";
import type { UserPublic } from "./user";

export const BookingStatus = {
  PENDING: "pending",
  CONFIRMED: "confirmed",
  CANCELLED: "cancelled",
} as const;

export type BookingStatusType =
  (typeof BookingStatus)[keyof typeof BookingStatus];

export interface BookingBase {
  occurrence_id: number;
}

export interface BookingCreate extends BookingBase {
  guest_name: string;
  guest_email: string;
  guest_phone?: string | null;
}

export interface BookingResponse extends BookingBase {
  id: number;
  user_id: number | null;
  guest_name: string | null;
  guest_email: string | null;
  guest_phone: string | null;
  status: string;
  payment_status: string | null;
  reserved_until: string | null;
  created_at: string;
  updated_at: string;
  cancelled_at: string | null;
  is_guest_booking?: boolean;
}

export interface BookingWithOccurrence extends BookingResponse {
  occurrence: OccurrenceResponse;
}

export interface BookingWithUser extends BookingResponse {
  user: UserPublic | null;
}

/** Self perspective list item from GET /bookings/my */
export interface BookingSelfListItem extends BookingResponse {
  occurrence: OccurrenceResponse;
  studio: StudioResponse;
}