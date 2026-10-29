export type NotificationCategory =
  | 'SYSTEM'
  | 'JOB_DRIVE'
  | 'APPLICATION'
  | 'INTERVIEW'
  | 'PLACEMENT'
  | 'FOLLOW_UP';

export interface NotificationItem {
  id: string;
  category: NotificationCategory;
  title: string;
  message: string;
  link: string;
  is_read: boolean;
  read_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface NotificationFilters {
  page?: number;
  page_size?: number;
  is_read?: boolean;
  category?: string;
}

export interface NotificationPaginationMeta {
  count: number;
  total_pages: number;
  current_page: number;
  next: string | null;
  previous: string | null;
}

export interface PaginatedNotificationsResponse {
  success: boolean;
  meta: NotificationPaginationMeta;
  data: NotificationItem[];
}

