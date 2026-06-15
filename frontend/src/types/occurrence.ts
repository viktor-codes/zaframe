/**
 * Occurrence types aligned with backend schemas.
 */

export interface OccurrenceBase {
  start_time: string;
  end_time: string;
  title: string;
  description?: string | null;
  max_capacity: number;
  price_cents: number;
}

export interface OccurrenceResponse extends OccurrenceBase {
  id: number;
  studio_id: number;
  status: "active" | "cancelled";
  created_at: string;
  updated_at: string;
}

export interface OccurrenceWithBookings extends OccurrenceResponse {
  bookings_count: number;
  available_spots: number;
}

export interface OccurrenceCreate extends OccurrenceBase {
  studio_id: number;
}

export interface OccurrenceUpdate {
  start_time?: string;
  end_time?: string;
  title?: string;
  description?: string | null;
  max_capacity?: number;
  price_cents?: number;
  status?: "active" | "cancelled";
}
