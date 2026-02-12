/**
 * Типы пользователя (по backend schemas).
 */

export interface UserBase {
  email: string;
  name: string;
  phone?: string | null;
}

export interface UserResponse extends UserBase {
  id: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface UserPublic extends UserBase {
  id: number;
  created_at: string;
}

export type UserCreate = UserBase;

export interface UserUpdate {
  email?: string;
  name?: string;
  phone?: string | null;
}
