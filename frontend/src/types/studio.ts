/**
 * Типы студии (по backend schemas).
 */

export interface StudioBase {
  name: string;
  description?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
}

export interface StudioResponse extends StudioBase {
  id: number;
  owner_id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StudioWithSlots extends StudioResponse {
  slots_count?: number | null;
}

export interface StudioCreate extends StudioBase {
  owner_id: number;
}

export interface StudioUpdate {
  name?: string;
  description?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
  is_active?: boolean;
}
