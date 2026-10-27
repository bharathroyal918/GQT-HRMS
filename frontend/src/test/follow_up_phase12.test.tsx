import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { FollowUpsPage } from '../pages/crm/FollowUpsPage';
import { apiClient } from '../lib/apiClient';

vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

describe('Phase 12: Automated Follow-Up Frontend Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Escalations tab and allows acknowledging and resolving an escalation case', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/crm/escalations/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'esc-101',
                case_type: 'OVERDUE_FOLLOW_UP',
                follow_up: 'fu-1',
                company_name: 'Oracle India',
                follow_up_purpose: 'Drive confirmation for 2026 CS cohort',
                follow_up_due_date: new Date(Date.now() - 86400000 * 4).toISOString(),
                escalated_to: 'user-head',
                escalated_to_name: 'Placement Director',
                escalated_to_email: 'director@gqt.local',
                escalated_by: null,
                previous_assigned_to: 'user-officer',
                previous_assigned_to_name: 'Officer User',
                reason: 'Follow-up is 4 days overdue without completion or rescheduling.',
                escalation_level: 'LEVEL_1',
                status: 'PENDING',
                acknowledged_at: null,
                acknowledged_by: null,
                acknowledged_by_name: null,
                resolved_at: null,
                resolved_by: null,
                resolved_by_name: null,
                resolution_notes: '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    vi.mocked(apiClient.post).mockImplementation((url: string) => {
      if (url.includes('/acknowledge/')) {
        return Promise.resolve({
          data: { success: true, message: 'Case escalation acknowledged successfully.' },
        });
      }
      if (url.includes('/resolve/')) {
        return Promise.resolve({
          data: { success: true, message: 'Case escalation resolved successfully.' },
        });
      }
      return Promise.resolve({ data: { success: true } });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/crm/follow-ups?tab=escalations']}>
          <FollowUpsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/SLA & Overdue Case Escalations/i)).toBeInTheDocument();
      expect(screen.getByText(/Oracle India/i)).toBeInTheDocument();
      expect(screen.getByText(/4 days overdue without completion/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Acknowledge$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Resolve Case$/i })).toBeInTheDocument();
    });

    // Test acknowledge action
    const ackButton = screen.getByRole('button', { name: /^Acknowledge$/i });
    fireEvent.click(ackButton);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/crm/escalations/esc-101/acknowledge/'),
        expect.anything()
      );
    });

    // Test open resolve modal
    const resolveButton = screen.getByRole('button', { name: /^Resolve Case$/i });
    fireEvent.click(resolveButton);

    expect(screen.getByText(/Resolve Case Escalation/i)).toBeInTheDocument();
    const notesInput = screen.getByPlaceholderText(/Document resolution outcome/i);
    fireEvent.change(notesInput, { target: { value: 'Spoke directly with Oracle HR director; drive scheduled.' } });

    const confirmResolve = screen.getByRole('button', { name: /^Confirm Resolution$/i });
    fireEvent.click(confirmResolve);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/crm/escalations/esc-101/resolve/'),
        expect.objectContaining({ resolution_notes: 'Spoke directly with Oracle HR director; drive scheduled.' })
      );
    });
  });

  it('renders Officer Alerts tab and allows marking notifications as read', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/crm/notifications/unread-count/')) {
        return Promise.resolve({ data: { success: true, count: 1 } });
      }
      if (url.includes('/crm/notifications/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'notif-201',
                recipient: 'officer-1',
                notification_type: 'FOLLOW_UP_DUE',
                title: 'Follow-Up Action Required Today',
                message: 'Follow-up for Capgemini is due today for 2026 Batch outreach.',
                link: '/crm/follow-ups?tab=today',
                follow_up: 'fu-2',
                company_name: 'Capgemini',
                is_read: false,
                read_at: null,
                created_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    vi.mocked(apiClient.post).mockImplementation((url: string) => {
      if (url.includes('/read/')) {
        return Promise.resolve({ data: { success: true, message: 'Notification marked as read.' } });
      }
      return Promise.resolve({ data: { success: true } });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/crm/follow-ups?tab=notifications']}>
          <FollowUpsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Placement Officer Automated Notifications/i)).toBeInTheDocument();
      expect(screen.getByText(/Follow-Up Action Required Today/i)).toBeInTheDocument();
      expect(screen.getByText(/Follow-up for Capgemini is due today/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Mark Read$/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Mark All Read$/i })).toBeInTheDocument();
    });

    const markReadBtn = screen.getByRole('button', { name: /^Mark Read$/i });
    fireEvent.click(markReadBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/crm/notifications/notif-201/read/')
      );
    });
  });

  it('renders reminder outbox details and allows retrying a failed reminder', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/crm/follow-ups/fu-3/reminders/')) {
        return Promise.resolve({
          data: {
            success: true,
            data: [
              {
                id: 'rem-301',
                follow_up: 'fu-3',
                follow_up_purpose: 'Schedule technical round',
                company_name: 'Cognizant',
                channel: 'EMAIL',
                recipient: 'recruiter@cognizant.com',
                recipient_name: 'Recruiter',
                scheduled_for: new Date().toISOString(),
                status: 'FAILED',
                attempt_count: 2,
                max_attempts: 3,
                backoff_until: null,
                sent_at: null,
                delivered_at: null,
                provider_message_id: '',
                error_message: 'SMTP connection timeout',
                is_simulated: false,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      if (url.includes('/crm/follow-ups/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'fu-3',
                company: { id: 'c3', name: 'Cognizant', domain_category: 'IT_SERVICES', relationship_status: 'ACTIVE_HIRING_PARTNER' },
                hr_contact: null,
                assigned_to: { id: 'u1', email: 'officer@gqt.local', first_name: 'Officer', last_name: 'User', full_name: 'Officer User' },
                category: 'INTERVIEW_CONFIRMATION',
                reminder_channel: 'EMAIL',
                remind_at: new Date().toISOString(),
                due_date: new Date(Date.now() + 86400000).toISOString(),
                priority: 'HIGH',
                status: 'OPEN',
                purpose: 'Schedule technical round for 2026 cohort',
                is_overdue: false,
                rescheduled_count: 0,
                completion_notes: '',
                completed_at: null,
                completed_by: null,
                cancellation_reason: '',
                created_by: null,
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: { success: true, data: [] } });
    });

    vi.mocked(apiClient.post).mockImplementation((url: string) => {
      if (url.includes('/retry/')) {
        return Promise.resolve({
          data: { success: true, message: 'Reminder retry scheduled.' },
        });
      }
      return Promise.resolve({ data: { success: true } });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/crm/follow-ups?tab=upcoming']}>
          <FollowUpsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Schedule technical round for 2026 cohort/i)).toBeInTheDocument();
      expect(screen.getByText(/EMAIL REMINDER/i)).toBeInTheDocument();
      expect(screen.getByText(/View Automated Reminder Outbox/i)).toBeInTheDocument();
    });

    const toggleOutbox = screen.getByText(/View Automated Reminder Outbox/i);
    fireEvent.click(toggleOutbox);

    await waitFor(() => {
      expect(screen.getByText(/Outbox Delivery Queue/i)).toBeInTheDocument();
      expect(screen.getByText(/recruiter@cognizant.com/i)).toBeInTheDocument();
      expect(screen.getByText(/SMTP connection timeout/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Retry$/i })).toBeInTheDocument();
    });

    const retryBtn = screen.getByRole('button', { name: /^Retry$/i });
    fireEvent.click(retryBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        expect.stringContaining('/crm/follow-ups/fu-3/reminders/rem-301/retry/')
      );
    });
  });

  it('allows opening Automation Cycle dialog and executing dry run', async () => {
    vi.mocked(apiClient.get).mockResolvedValue({
      data: {
        success: true,
        meta: { count: 0, total_pages: 1, current_page: 1, next: null, previous: null },
        data: [],
      },
    });

    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          success: true,
          dry_run: true,
          correlation_id: 'corr-test-123',
          executed_at: new Date().toISOString(),
          reminders_eligible: 3,
          due_notifications_eligible: 2,
          overdue_escalations_eligible: 1,
        },
      },
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/crm/follow-ups?tab=overdue']}>
          <FollowUpsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^Automation Cycle$/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /^Automation Cycle$/i }));

    expect(screen.getByText(/Run Automation Follow-up Cycle/i)).toBeInTheDocument();
    const dryRunCheckbox = screen.getByLabelText(/Dry Run Mode/i);
    fireEvent.click(dryRunCheckbox);

    const executeBtn = screen.getByRole('button', { name: /^Execute Cycle$/i });
    fireEvent.click(executeBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/crm/automation/run/', { dry_run: true });
      expect(screen.getByText(/Execution Result:/i)).toBeInTheDocument();
      expect(screen.getByText(/Dry Run/i)).toBeInTheDocument();
    });
  });
});
