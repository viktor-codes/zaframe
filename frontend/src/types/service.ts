/**
 * Типы услуг (по backend schemas).
 */

export type ServiceCategory =
  | "yoga"
  | "boxing"
  | "dance"
  | "hiit"
  | "pilates"
  | "martial_arts"
  | "strength";

export interface ServiceResponse {
  id: number;
  studio_id: number;
  name: string;
  description?: string | null;
  type: string;
  category: ServiceCategory;
  tags: string[];
  duration_minutes: number;
  max_capacity: number;
  price_single_cents: number;
  price_course_cents?: number | null;
  soft_limit_ratio: number;
  hard_limit_ratio: number;
  max_overbooked_ratio: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
