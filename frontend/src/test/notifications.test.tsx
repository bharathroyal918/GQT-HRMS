import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NotificationBell } from '../components/notifications/NotificationBell';
import { NotificationsPage } from '../pages/notifications/NotificationsPage';
import { notificationsApi } from '../api/notificationsApi';
import { NotificationItem, PaginatedNotificationsResponse } from '../types/notifications';

vi.mock('../api/notificationsApi', () => ({
  notificationsApi: {
    listNotifications: vi.fn(),
    getUnreadCount: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
  },
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

const mockNotifications: NotificationItem[] = [
  {
    id: 'notif-001',
    category: 'JOB_DRIVE',
    title: 'New Drive: Google Software Engineer',
    message: 'Google is hosting on-campus recruitment for 2026 graduates.',
    link: '/students/drives',
    is_read: false,
    read_at: null,
    metadata: { job_id: 'job-1' },
    created_at: new Date(Date.now() - 1000 * 60 * 10).toISOString(), // 10 mins ago
  },
  {
    id: 'notif-002',
    category: 'APPLICATION',
    title: 'Application Received: Microsoft',
    message: 'Your drive application has been evaluated as ELIGIBLE.',
    link: '/students/drives',
    is_read: false,
    read_at: null,
    metadata: { app_id: 'app-1' },
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
  },
  {
    id: 'notif-003',
    category: 'FOLLOW_UP',
    title: 'Follow-Up Assigned: Amazon',
    message: 'HR outreach follow-up is scheduled for tomorrow.',
    link: '/crm/follow-ups',
    is_read: true,
    read_at: new Date().toISOString(),
    metadata: {},
    created_at: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
  },
];

const mockPaginatedResponse: PaginatedNotificationsResponse = {
  success: true,
  meta: {
    count: 3,
    total_pages: 1,
    current_page: 1,
    next: null,
    previous: null,
  },
  data: mockNotifications,
};

describe('Global Notification Center Frontend Suite (Phase 15 WS3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('NotificationBell Component', () => {
    it('renders bell button and displays unread badge when unreadCount > 0', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      const bellBtn = screen.getByRole('button', { name: /notifications/i });
      expect(bellBtn).toBeInTheDocument();

      const badge = await screen.findByTestId('unread-badge');
      expect(badge).toHaveTextContent('2');
    });

    it('toggles dropdown panel on click and displays notification items', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      const bellBtn = screen.getByRole('button', { name: /notifications/i });
      fireEvent.click(bellBtn);

      const dropdown = await screen.findByTestId('notifications-dropdown');
      expect(dropdown).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'Notifications' })).toBeInTheDocument();
      expect(await screen.findByText(/New Drive: Google Software Engineer/i)).toBeInTheDocument();
      expect(screen.getByText(/Application Received: Microsoft/i)).toBeInTheDocument();
      expect(screen.getByText(/View all notifications/i)).toBeInTheDocument();
    });

    it('allows marking an individual notification as read from the dropdown', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);
      const firstNotif = mockNotifications[0]!;
      vi.mocked(notificationsApi.markAsRead).mockResolvedValue({
        success: true,
        data: { ...firstNotif, is_read: true, read_at: new Date().toISOString() },
      });

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
      await screen.findByTestId('notifications-dropdown');

      const markReadButtons = await screen.findAllByTitle('Mark as read');
      expect(markReadButtons.length).toBeGreaterThanOrEqual(1);

      const targetBtn = markReadButtons[0];
      expect(targetBtn).toBeDefined();
      fireEvent.click(targetBtn!);
      await waitFor(() => {
        expect(notificationsApi.markAsRead).toHaveBeenCalledWith('notif-001');
      });
    });

    it('allows marking all notifications as read from the dropdown', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);
      vi.mocked(notificationsApi.markAllAsRead).mockResolvedValue({ success: true, count: 2 });

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
      await screen.findByTestId('notifications-dropdown');

      const markAllBtn = await screen.findByRole('button', { name: /mark all read/i });
      fireEvent.click(markAllBtn);

      await waitFor(() => {
        expect(notificationsApi.markAllAsRead).toHaveBeenCalled();
      });
    });

    it('renders empty state when there are zero notifications', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 0 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue({
        success: true,
        meta: { count: 0, total_pages: 0, current_page: 1, next: null, previous: null },
        data: [],
      });

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
      await screen.findByTestId('notifications-dropdown');

      expect(await screen.findByText(/No notifications/i)).toBeInTheDocument();
      expect(screen.getByText(/You are all caught up with your updates/i)).toBeInTheDocument();
    });

    it('renders error state and retry button on fetch failure', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 1 });
      vi.mocked(notificationsApi.listNotifications).mockRejectedValue(new Error('Network error'));

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationBell />
          </MemoryRouter>
        </QueryClientProvider>
      );

      fireEvent.click(screen.getByRole('button', { name: /notifications/i }));
      await screen.findByTestId('notifications-dropdown');

      expect(await screen.findByText(/Failed to load notifications/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    });
  });

  describe('NotificationsPage Component', () => {
    it('renders full notification directory and category filter tabs', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationsPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      expect(await screen.findByRole('heading', { name: 'Notification Center' })).toBeInTheDocument();
      expect(screen.getByText('All Notifications')).toBeInTheDocument();
      expect(screen.getByText('Job Drives')).toBeInTheDocument();
      expect(screen.getByText('Applications')).toBeInTheDocument();
      expect(screen.getByText('Follow-ups')).toBeInTheDocument();

      expect(await screen.findByText(/New Drive: Google Software Engineer/i)).toBeInTheDocument();
      expect(screen.getByText(/Application Received: Microsoft/i)).toBeInTheDocument();
      expect(screen.getByText(/Follow-Up Assigned: Amazon/i)).toBeInTheDocument();
    });

    it('switching filter tabs executes filtered API queries', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationsPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      await screen.findByRole('heading', { name: 'Notification Center' });
      await screen.findByText(/New Drive: Google Software Engineer/i);

      // Click "Job Drives" tab
      fireEvent.click(screen.getByText('Job Drives'));

      await waitFor(() => {
        expect(notificationsApi.listNotifications).toHaveBeenCalledWith(
          expect.objectContaining({ category: 'JOB_DRIVE', page: 1 })
        );
      });
    });

    it('triggers mark-all-read action from the page header button', async () => {
      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 2 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(mockPaginatedResponse);
      vi.mocked(notificationsApi.markAllAsRead).mockResolvedValue({ success: true, count: 2 });

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationsPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      const markAllBtn = await screen.findByRole('button', { name: /Mark All as Read \(2\)/i });
      fireEvent.click(markAllBtn);

      await waitFor(() => {
        expect(notificationsApi.markAllAsRead).toHaveBeenCalled();
      });
    });

    it('renders pagination bar when total pages > 1 and handles page transitions', async () => {
      const multiPageResponse: PaginatedNotificationsResponse = {
        success: true,
        meta: {
          count: 30,
          total_pages: 2,
          current_page: 1,
          next: 'http://localhost:8000/api/v1/notifications/?page=2',
          previous: null,
        },
        data: mockNotifications,
      };

      vi.mocked(notificationsApi.getUnreadCount).mockResolvedValue({ success: true, count: 0 });
      vi.mocked(notificationsApi.listNotifications).mockResolvedValue(multiPageResponse);

      const queryClient = createTestQueryClient();
      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter>
            <NotificationsPage />
          </MemoryRouter>
        </QueryClientProvider>
      );

      expect(await screen.findByText(/Showing page/i)).toBeInTheDocument();
      const nextBtn = screen.getByRole('button', { name: /next/i });
      expect(nextBtn).toBeEnabled();

      fireEvent.click(nextBtn);
      await waitFor(() => {
        expect(notificationsApi.listNotifications).toHaveBeenCalledWith(
          expect.objectContaining({ page: 2 })
        );
      });
    });
  });
});

