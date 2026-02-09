/**
 * Типы слота (расписание) по backend schemas.
 */

export interface SlotBase {
  start_time: string;
  end_time: string;
  title: string;
  description?: string | null;
  max_capacity: number;
  price_cents: number;
}

export interface SlotResponse extends SlotBase {
  id: number;
  studio_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SlotWithBookings extends SlotResponse {
  bookings_count: number;
  available_spots: number;
}

export interface SlotCreate extends SlotBase {
  studio_id: number;
}

export interface SlotUpdate {
  start_time?: string;
  end_time?: string;
  title?: string;
  description?: string | null;
  max_capacity?: number;
  price_cents?: number;
  is_active?: boolean;
}
