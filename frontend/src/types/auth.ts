/**
 * Authentication and Role-Based Access Control type definitions.
 */

export interface Role {
  id: string;
  code: string;
  name: string;
  description: string;
  is_active: boolean;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles: string[];
  created_at: string;
  last_login: string | null;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface PasswordChangePayload {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export interface PasswordResetRequestPayload {
  email: string;
}

export interface PasswordResetConfirmPayload {
  uidb64: string;
  token: string;
  new_password: string;
  new_password_confirm: string;
}
