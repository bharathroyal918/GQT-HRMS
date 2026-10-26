import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { JobDirectoryPage } from '../pages/jobs/JobDirectoryPage';
import { JobDetailPage } from '../pages/jobs/JobDetailPage';
import { JobApprovalsQueuePage } from '../pages/jobs/JobApprovalsQueuePage';
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

describe('Frontend Job Requirements & Verification Suite (Phase 3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Job Directory with KPI metrics and requirements table', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'officer-1',
            email: 'officer@gqt.local',
            roles: ['PLACEMENT_OFFICER', 'PLACEMENT_HEAD'],
            full_name: 'Officer User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url === '/jobs/requirements/') {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'job-1',
                title: 'Associate Cloud Engineer',
                company: 'comp-1',
                company_name: 'Wipro Limited',
                company_tier: 'TIER_1',
                hr_contact: 'hr-1',
                hr_contact_name: 'Anjali Gupta',
                location: 'Bangalore',
                work_arrangement: 'HYBRID',
                employment_type: 'FULL_TIME',
                min_salary: '600000.00',
                max_salary: '850000.00',
                salary_currency: 'INR',
                status: 'UNDER_REVIEW',
                registration_deadline: new Date(Date.now() + 86400000 * 10).toISOString(),
                openings_count: 10,
                checklist_progress: {
                  total_mandatory: 5,
                  verified_mandatory: 3,
                  percentage: 60,
                  is_complete: false,
                },
                is_archived: false,
                created_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      if (url === '/jobs/requirements/metrics/') {
        return Promise.resolve({
          data: {
            total_active: 12,
            draft_count: 2,
            pending_verification_count: 4,
            under_review_count: 2,
            changes_requested_count: 1,
            verified_count: 1,
            approved_count: 2,
            rejected_count: 0,
            deadlines_approaching_count: 3,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <JobDirectoryPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Loading job requirement directory.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/Job Requirements & Verification/i)).toBeInTheDocument();
      expect(screen.getByText('Associate Cloud Engineer')).toBeInTheDocument();
      expect(screen.getByText('Wipro Limited')).toBeInTheDocument();
      expect(screen.getByText(/3 \/ 5 Verified/i)).toBeInTheDocument();
    });
  });

  it('renders Job Detail workspace with 5-point verification checklist items', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'officer-1',
            email: 'officer@gqt.local',
            roles: ['PLACEMENT_OFFICER', 'PLACEMENT_HEAD'],
            full_name: 'Officer User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url.includes('/jobs/requirements/')) {
        return Promise.resolve({
          data: {
            id: 'job-1',
            company: 'comp-1',
            company_name: 'Infosys BPM',
            company_website: 'https://infosys.com',
            company_domain: 'infosys.com',
            company_tier: 'TIER_1',
            company_category: 'IT_SERVICES',
            hr_contact: 'hr-1',
            hr_contact_name: 'Rajesh Nair',
            hr_contact_email: 'rajesh@infosys.com',
            hr_contact_phone: '+919988776655',
            title: 'Software Developer Trainee',
            job_description: 'Full stack development role in Java and Angular.',
            skills_required: 'Java, Spring Boot, Angular',
            min_salary: '450000.00',
            max_salary: '600000.00',
            salary_currency: 'INR',
            salary_breakup: 'Fixed: 4.5 LPA, Variable: 1.5 LPA',
            location: 'Mysore / Bangalore',
            work_arrangement: 'ON_SITE',
            employment_type: 'FULL_TIME',
            has_bond: true,
            bond_details: '12-month training agreement',
            eligibility_criteria: 'BE/B.Tech with 60% aggregate',
            min_cgpa: '6.00',
            hiring_process: 'Round 1: Online Test, Round 2: Technical Interview',
            interview_date: '2026-11-15',
            registration_deadline: new Date(Date.now() + 86400000 * 7).toISOString(),
            openings_count: 25,
            status: 'UNDER_REVIEW',
            created_by: 'user-1',
            created_by_name: 'Placement Team',
            assigned_verifier: null,
            assigned_verifier_name: '',
            verified_by: null,
            verified_by_name: '',
            verified_at: null,
            approved_by: null,
            approved_by_name: '',
            approved_at: null,
            rejection_reason: '',
            return_reason: '',
            notes: '',
            is_archived: false,
            checklist_items: [
              {
                id: 'item-1',
                item_code: 'ELIGIBILITY',
                title: 'Candidate Academic & Degree Eligibility',
                description: 'Verify eligible academic branches, minimum CGPA/percentage cutoff...',
                is_mandatory: true,
                status: 'VERIFIED',
                verified_by: 'user-2',
                verified_by_name: 'Placement Officer',
                verified_at: new Date().toISOString(),
                remarks: '60% cutoff verified',
              },
              {
                id: 'item-2',
                item_code: 'SALARY_AUTHENTICITY',
                title: 'Salary Package & CTC Authenticity',
                description: 'Verify gross vs. net CTC breakdown...',
                is_mandatory: true,
                status: 'PENDING',
                verified_by: null,
                verified_by_name: '',
                verified_at: null,
                remarks: '',
              },
              {
                id: 'item-3',
                item_code: 'COMPANY_AUTHENTICITY',
                title: 'Company Authenticity & Hiring Legitimacy',
                description: 'Confirm legitimate corporate entity registration...',
                is_mandatory: true,
                status: 'PENDING',
                verified_by: null,
                verified_by_name: '',
                verified_at: null,
                remarks: '',
              },
              {
                id: 'item-4',
                item_code: 'INTERVIEW_PROCESS',
                title: 'Interview & Selection Process Clarity',
                description: 'Verify the complete sequence of evaluation stages...',
                is_mandatory: true,
                status: 'PENDING',
                verified_by: null,
                verified_by_name: '',
                verified_at: null,
                remarks: '',
              },
              {
                id: 'item-5',
                item_code: 'REGISTRATION_DEADLINE',
                title: 'Registration Deadline & Drive Timelines',
                description: 'Verify reasonable student application turnaround time...',
                is_mandatory: true,
                status: 'PENDING',
                verified_by: null,
                verified_by_name: '',
                verified_at: null,
                remarks: '',
              },
            ],
            decisions: [],
            checklist_progress: {
              total_mandatory: 5,
              verified_mandatory: 1,
              percentage: 20,
              is_complete: false,
            },
            is_locked: false,
            is_editable: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/jobs/job-1']}>
            <Routes>
              <Route path="/jobs/:id" element={<JobDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Software Developer Trainee')).toBeInTheDocument();
      expect(screen.getByText(/Infosys BPM/i)).toBeInTheDocument();
      expect(screen.getByText('Candidate Academic & Degree Eligibility')).toBeInTheDocument();
      expect(screen.getByText('Salary Package & CTC Authenticity')).toBeInTheDocument();
      expect(screen.getByText('Company Authenticity & Hiring Legitimacy')).toBeInTheDocument();
      expect(screen.getByText('Interview & Selection Process Clarity')).toBeInTheDocument();
      expect(screen.getByText('Registration Deadline & Drive Timelines')).toBeInTheDocument();
      expect(screen.getByText(/1 of 5 points passed/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Approve Opportunity/i })).toBeDisabled();
    });
  });

  it('renders Review & Approvals operational queues', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'officer-1',
            email: 'officer@gqt.local',
            roles: ['PLACEMENT_OFFICER', 'PLACEMENT_HEAD'],
            full_name: 'Officer User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url.includes('/pending-verification/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'job-v1',
                title: 'Data Science Intern',
                company: 'comp-2',
                company_name: 'Mu Sigma',
                company_tier: 'TIER_2',
                hr_contact: null,
                hr_contact_name: '',
                location: 'Bangalore',
                work_arrangement: 'ON_SITE',
                employment_type: 'INTERNSHIP',
                min_salary: '300000.00',
                max_salary: '400000.00',
                salary_currency: 'INR',
                status: 'PENDING_VERIFICATION',
                registration_deadline: new Date(Date.now() + 86400000 * 5).toISOString(),
                openings_count: 5,
                checklist_progress: {
                  total_mandatory: 5,
                  verified_mandatory: 0,
                  percentage: 0,
                  is_complete: false,
                },
                is_archived: false,
                created_at: new Date().toISOString(),
              },
            ],
          },
        });
      }
      if (url.includes('/pending-approval/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 0, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [],
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <JobApprovalsQueuePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Review & Approval Workspace/i)).toBeInTheDocument();
      expect(screen.getByText(/Step 6: Checklist Audit Queue/i)).toBeInTheDocument();
      expect(screen.getByText(/Step 7: Head Approval Queue/i)).toBeInTheDocument();
      expect(screen.getByText('Data Science Intern')).toBeInTheDocument();
      expect(screen.getByText('Mu Sigma')).toBeInTheDocument();
    });
  });

  it('enforces role-based route guard and blocks unauthorized student access', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'student-1',
            email: 'student@gqt.local',
            first_name: 'Aditi',
            last_name: 'Verma',
            full_name: 'Aditi Verma',
            roles: ['STUDENT'],
            is_active: true,
            is_staff: false,
            is_superuser: false,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/jobs']}>
            <Routes>
              <Route
                path="/jobs"
                element={
                  <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']}>
                    <div>Protected Job Management Content</div>
                  </ProtectedRoute>
                }
              />
              <Route path="/access-denied" element={<div>Access Denied Screen</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Access Denied Screen/i)).toBeInTheDocument();
      expect(screen.queryByText(/Protected Job Management Content/i)).not.toBeInTheDocument();
    });
  });
});
