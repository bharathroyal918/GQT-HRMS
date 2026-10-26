import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CrmDashboardPage } from '../pages/crm/CrmDashboardPage';
import { CompaniesPage } from '../pages/crm/CompaniesPage';
import { CompanyFormPage } from '../pages/crm/CompanyFormPage';
import { FollowUpsPage } from '../pages/crm/FollowUpsPage';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { AuthProvider } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
  },
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

describe('Frontend Corporate CRM Suite (Phase 2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders CRM Dashboard with KPI cards and 100/day target benchmark', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: {
          total_active_companies: 42,
          total_active_contacts: 85,
          daily_outreach_target: 100,
          today_outreach_count: 24,
          today_outreach_progress_percent: 24.0,
          channel_breakdown: { CALL: 12, EMAIL: 8, LINKEDIN: 4 },
          user_today_outreach_count: 15,
          follow_ups_due_today: 7,
          follow_ups_overdue: 3,
          follow_ups_completed: 18,
          timezone: 'Asia/Kolkata',
          as_of: new Date().toISOString(),
          recent_activities: [
            {
              id: 'activity-1',
              channel: 'CALL',
              direction: 'OUTBOUND',
              activity_date: new Date().toISOString(),
              outcome: 'CONNECTED_INTERESTED',
              subject: 'Campus drive discussion',
              company__id: 'comp-1',
              company__name: 'Infosys',
              hr_contact__id: 'cont-1',
              hr_contact__name: 'Sunita',
              performed_by__email: 'recruiter@gqt.local',
              performed_by__first_name: 'Priya',
              performed_by__last_name: 'Sharma',
            },
          ],
        },
      },
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CrmDashboardPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Loading Corporate CRM operational metrics.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Corporate CRM & HR Directory/i)).toBeInTheDocument();
      expect(screen.getByText('42')).toBeInTheDocument();
      expect(screen.getByText('85')).toBeInTheDocument();
      expect(screen.getByText(/Daily Outreach Benchmark/i)).toBeInTheDocument();
      expect(screen.getByText('Infosys')).toBeInTheDocument();
    });
  });

  it('renders Company directory with filterable table and pagination', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        meta: {
          count: 1,
          total_pages: 1,
          current_page: 1,
          next: null,
          previous: null,
        },
        data: [
          {
            id: 'comp-123',
            name: 'Wipro Technologies',
            normalized_name: 'wipro technologies',
            website: 'https://wipro.com',
            domain: 'wipro.com',
            domain_category: 'IT_SERVICES',
            tier: 'TIER_1',
            relationship_status: 'ACTIVE_HIRING_PARTNER',
            source: 'MARKET_RESEARCH',
            city: 'Bengaluru',
            state: 'Karnataka',
            country: 'India',
            owner: null,
            hr_contacts_count: 5,
            is_archived: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ],
      },
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CompaniesPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Corporate Directory/i)).toBeInTheDocument();
      expect(screen.getByText(/Wipro Technologies/i)).toBeInTheDocument();
      expect(screen.getAllByText(/IT Services/i).length).toBeGreaterThanOrEqual(1);
    });
  });

  it('detects and displays duplicate warning candidates when creating a company', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        data: [
          {
            company_id: 'existing-123',
            name: 'Tata Consultancy Services',
            domain: 'tcs.com',
            relationship_status: 'ACTIVE_HIRING_PARTNER',
            is_archived: false,
            match_type: 'EXACT_NAME',
            reason: 'Existing record has matching normalized company name',
          },
        ],
      },
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <CompanyFormPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    const nameInput = screen.getByPlaceholderText(/e.g. Tata Consultancy Services Ltd./i);
    fireEvent.change(nameInput, { target: { value: 'Tata Consultancy Services' } });

    await waitFor(
      () => {
        expect(screen.getByText(/Potential Duplicate Company Detected/i)).toBeInTheDocument();
        expect(screen.getByText(/Existing record has matching normalized company name/i)).toBeInTheDocument();
      },
      { timeout: 2000 }
    );
  });

  it('renders Follow-Up workspace with overdue and due today tabs', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        success: true,
        meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
        data: [
          {
            id: 'follow-1',
            company: { id: 'c1', name: 'Infosys', domain_category: 'IT_SERVICES', relationship_status: 'DISCOVERED' },
            hr_contact: { id: 'h1', name: 'Sunita', designation: 'Lead HR', email: 's@infosys.com', phone: '', status: 'ACTIVE', is_archived: false },
            assigned_to: { id: 'u1', email: 'officer@gqt.local', first_name: 'Officer', last_name: 'User', full_name: 'Officer User' },
            due_date: new Date(Date.now() - 3600000).toISOString(),
            priority: 'HIGH',
            status: 'OPEN',
            purpose: 'Urgent callback requested regarding 2026 CS drive',
            is_overdue: true,
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

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/crm/follow-ups?tab=overdue']}>
          <FollowUpsPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Corporate Follow-Up Workspace/i)).toBeInTheDocument();
      expect(screen.getByText(/Urgent callback requested regarding 2026 CS drive/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /^Complete$/i })).toBeInTheDocument();
    });
  });

  it('enforces RBAC guard on ProtectedRoute denying students from CRM', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        id: 'student-id',
        email: 'student@gqt.local',
        roles: ['STUDENT'],
        full_name: 'Student User',
      },
    });

    render(
      <MemoryRouter initialEntries={['/crm']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/crm"
              element={
                <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'AUDITOR']}>
                  <div>Protected CRM Workspace</div>
                </ProtectedRoute>
              }
            />
            <Route path="/access-denied" element={<div>Access Denied Page</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Access Denied Page/i)).toBeInTheDocument();
      expect(screen.queryByText(/Protected CRM Workspace/i)).not.toBeInTheDocument();
    });
  });
});
