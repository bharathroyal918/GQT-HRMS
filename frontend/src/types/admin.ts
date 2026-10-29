import { User, Role } from './auth';

export interface AdminUserFilters {
  search?: string;
  role?: string;
  status?: 'active' | 'inactive' | '';
  ordering?: string;
  page?: number;
  page_size?: number;
}

export interface UserCreatePayload {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone_number?: string;
  is_active?: boolean;
  roles?: string[];
}

export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone_number?: string;
}

export interface UserStatusPayload {
  is_active: boolean;
}

export interface UserRoleAssignPayload {
  role_codes: string[];
}

export interface UserAuditLog {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  actor_email: string;
  actor_name: string;
  ip_address: string | null;
  user_agent: string;
  correlation_id: string;
  changes: Record<string, any>;
  created_at: string;
}

export interface PaginatedUsersResponse {
  success: boolean;
  meta: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  data: User[];
}

export interface PaginatedAuditLogsResponse {
  success: boolean;
  meta: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  data: UserAuditLog[];
}

export type { User, Role };

