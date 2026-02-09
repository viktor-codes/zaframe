/**
 * Типы бронирования по backend schemas.
 */

import type { SlotResponse } from "./slot";
import type { UserPublic } from "./user";

export const BookingStatus = {
  PENDING: "pending",
  CONFIRMED: "confirmed",
  CANCELLED: "cancelled",
} as const;

export type BookingStatusType = (typeof BookingStatus)[keyof typeof BookingStatus];

export interface BookingBase {
  slot_id: number;
}

export interface BookingCreate extends BookingBase {
  guest_name: string;
  guest_email: string;
  guest_phone?: string | null;
}

export interface BookingResponse extends BookingBase {
  id: number;
  user_id: number | null;
  guest_session_id: string | null;
  guest_name: string | null;
  guest_email: string | null;
  guest_phone: string | null;
  status: string;
  checkout_session_id: string | null;
  payment_intent_id: string | null;
  payment_status: string | null;
  created_at: string;
  updated_at: string;
  cancelled_at: string | null;
}

export interface BookingWithSlot extends BookingResponse {
  slot: SlotResponse;
}

export interface BookingWithUser extends BookingResponse {
  user: UserPublic | null;
}
