import { apiClient } from '@/lib/apiClient';
import {
  NotificationFilters,
  NotificationItem,
  PaginatedNotificationsResponse,
} from '@/types/notifications';

export const notificationsApi = {
  /**
   * List authenticated user notifications with optional pagination, is_read, and category filters.
   */
  async listNotifications(filters?: NotificationFilters): Promise<PaginatedNotificationsResponse> {
    const params = new URLSearchParams();
    if (filters?.page) params.append('page', String(filters.page));
    if (filters?.page_size) params.append('page_size', String(filters.page_size));
    if (filters?.is_read !== undefined) params.append('is_read', String(filters.is_read));
    if (filters?.category) params.append('category', filters.category);

    const query = params.toString();
    const endpoint = query ? `/notifications/?${query}` : '/notifications/';
    const response = await apiClient.get<PaginatedNotificationsResponse>(endpoint);
    return response.data;
  },

  /**
   * Retrieve unread notification count for badge.
   */
  async getUnreadCount(): Promise<{ success: boolean; count: number }> {
    const response = await apiClient.get<{ success: boolean; count: number }>('/notifications/unread-count/');
    return response.data;
  },

  /**
   * Mark a single notification as read.
   */
  async markAsRead(id: string): Promise<{ success: boolean; data: NotificationItem }> {
    const response = await apiClient.post<{ success: boolean; data: NotificationItem }>(
      `/notifications/${id}/read/`
    );
    return response.data;
  },

  /**
   * Mark all unread notifications for authenticated user as read.
   */
  async markAllAsRead(): Promise<{ success: boolean; count: number; message?: string }> {
    const response = await apiClient.post<{ success: boolean; count: number; message?: string }>(
      '/notifications/mark-all-read/'
    );
    return response.data;
  },
};

