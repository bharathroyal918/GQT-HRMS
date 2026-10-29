import { apiClient } from '@/lib/apiClient';
import {
  AdminUserFilters,
  PaginatedAuditLogsResponse,
  PaginatedUsersResponse,
  Role,
  User,
  UserCreatePayload,
  UserRoleAssignPayload,
  UserStatusPayload,
  UserUpdatePayload,
} from '@/types/admin';

export const usersApi = {
  /**
   * List user accounts with server-side pagination, search, status, role, and ordering filters.
   */
  async listUsers(filters?: AdminUserFilters): Promise<PaginatedUsersResponse> {
    const params = new URLSearchParams();
    if (filters?.search) params.append('search', filters.search);
    if (filters?.role) params.append('role', filters.role);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.ordering) params.append('ordering', filters.ordering);
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));

    const query = params.toString();
    const endpoint = query ? `/auth/users/?${query}` : '/auth/users/';
    const response = await apiClient.get<PaginatedUsersResponse>(endpoint);
    return response.data;
  },

  /**
   * Retrieve a single user account by UUID.
   */
  async getUser(id: string): Promise<User> {
    const response = await apiClient.get<User>(`/auth/users/${id}/`);
    return response.data;
  },

  /**
   * Provision a new user account with initial role assignments.
   */
  async createUser(payload: UserCreatePayload): Promise<User> {
    const response = await apiClient.post<User>('/auth/users/', payload);
    return response.data;
  },

  /**
   * Update permitted profile details (first_name, last_name, phone_number).
   */
  async updateUser(id: string, payload: UserUpdatePayload): Promise<User> {
    const response = await apiClient.patch<User>(`/auth/users/${id}/`, payload);
    return response.data;
  },

  /**
   * Activate or deactivate a user account with safety guards.
   */
  async updateUserStatus(id: string, payload: UserStatusPayload): Promise<User> {
    const response = await apiClient.patch<User>(`/auth/users/${id}/status/`, payload);
    return response.data;
  },

  /**
   * Assign or revoke operational roles for a user account.
   */
  async assignUserRoles(id: string, payload: UserRoleAssignPayload): Promise<{ roles: string[] }> {
    const response = await apiClient.post<{ roles: string[] }>(`/auth/users/${id}/roles/`, payload);
    return response.data;
  },

  /**
   * List all authoritative operational roles from the RoleCatalog.
   */
  async listRoles(): Promise<Role[]> {
    const response = await apiClient.get<Role[]>('/auth/roles/');
    return response.data;
  },

  /**
   * Retrieve paginated, immutable audit history for a user account.
   */
  async getUserAuditLogs(id: string, page = 1): Promise<PaginatedAuditLogsResponse> {
    const response = await apiClient.get<PaginatedAuditLogsResponse>(
      `/auth/users/${id}/audit-logs/?page=${page}`
    );
    return response.data;
  },
};

