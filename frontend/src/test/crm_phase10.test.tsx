import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CrmReconciliationPage } from '../pages/crm/CrmReconciliationPage';
import { CompanyDetailPage } from '../pages/crm/CompanyDetailPage';
import { StudentDirectoryPage } from '../pages/students/StudentDirectoryPage';
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

const mockAdminUser = {
  id: 'user-admin-1',
  email: 'admin@gqt.local',
  roles: ['ADMIN'],
  full_name: 'System Admin',
  is_staff: true,
};

const mockAuditorUser = {
  id: 'user-auditor-1',
  email: 'auditor@gqt.local',
  roles: ['AUDITOR'],
  full_name: 'Independent Auditor',
  is_staff: false,
};

const mockDiagnosticsReport = {
  summary: {
    total_records_checked: 80,
    total_consistent_records: 78,
    total_conflicts: 2,
    health_score_percentage: 97.5,
    status: 'NEEDS_ATTENTION',
    as_of: new Date().toISOString(),
  },
  areas: {
    company: { name: 'Company', total: 10, consistent: 9, conflicts: 1, status: 'WARNING' },
    hr: { name: 'HR Contacts', total: 15, consistent: 15, conflicts: 0, status: 'CLEAN' },
    students: { name: 'Students', total: 20, consistent: 19, conflicts: 1, status: 'WARNING' },
    resumes: { name: 'Resume Versions', total: 10, consistent: 10, confSlicts: 0, status: 'CLEAN' },
    interviews: { name: 'Interview Status', total: 8, consistent: 8, conflicts: 0, status: 'CLEAN' },
    placements: { name: 'Placement Status', total: 5, consistent: 5, conflicts: 0, status: 'CLEAN' },
    feedback: { name: 'Feedback', total: 7, consistent: 7, conflicts: 0, status: 'CLEAN' },
    communications: { name: 'Communication History', total: 5, consistent: 5, conflicts: 0, status: 'CLEAN' },
  },
  conflicts: [
    {
      area: 'Company',
      severity: 'WARNING',
      resource_type: 'Company',
      resource_id: 'comp-unpromoted-1',
      description: "Company 'TCS' has placed candidate records but relationship_status is 'CONNECTED' instead of 'ACTIVE_HIRING_PARTNER'.",
      recommended_action: "Promote relationship_status to 'ACTIVE_HIRING_PARTNER' during reconciliation.",
    },
    {
      area: 'Students',
      severity: 'WARNING',
      resource_type: 'StudentProfile',
      resource_id: 'stud-cgpa-invalid',
      description: "Student '1GQ22CS099' has invalid CGPA 12.5 (must be between 0.00 and 10.00).",
      recommended_action: 'Correct CGPA value to valid 0.00–10.00 academic scale.',
    },
  ],
};

const mockReconciliationHistory = [
  {
    id: 'run-001',
    triggered_by: 'user-admin-1',
    triggered_by_name: 'System Admin',
    triggered_by_email: 'admin@gqt.local',
    status: 'COMPLETED',
    total_records_checked: 80,
    conflicts_detected: 2,
    records_synchronized: 1,
    diagnostic_details: {},
    summary: 'Promoted 1 verified placement partner companies to ACTIVE_HIRING_PARTNER.',
    created_at: new Date().toISOString(),
  },
];

const mockCompany360 = {
  company: {
    id: 'comp-001',
    name: 'Tata Consultancy Services',
    domain: 'tcs.com',
    domain_category: 'IT_SERVICES',
    tier: 'TIER_1',
    relationship_status: 'ACTIVE_HIRING_PARTNER',
    relationship_status_display: 'Active Hiring Partner',
    city: 'Bengaluru',
    state: 'Karnataka',
    owner_name: 'Priya Sharma',
  },
  hr_contacts: [
    {
      id: 'cont-001',
      name: 'Sunita Rao',
      designation: 'Campus Lead',
      department: 'HR',
      email: 'sunita.rao@tcs.com',
      phone: '+91 98765 43210',
      preferred_channel: 'EMAIL',
      status: 'ACTIVE',
    },
  ],
  lifetime_metrics: {
    total_jobs: 3,
    total_submissions: 45,
    total_interviewed: 20,
    total_placed: 8,
    total_joined: 6,
    avg_offered_ctc: 750000.0,
    total_hr_feedbacks: 4,
    total_student_feedbacks: 12,
  },
  feedback_summary: {
    total_hr_evaluations: 4,
    avg_technical_skills_rating: 4.5,
    avg_communication_skills_rating: 4.2,
    avg_hiring_satisfaction_rating: 4.8,
    difficulty_breakdown: { EASY: 1, MEDIUM: 8, HARD: 3, VERY_HARD: 0 },
  },
  recruitment_drives: [
    {
      id: 'drive-001',
      title: 'TCS Ninja & Digital 2026 Drive',
      status: 'APPROVED',
      openings_count: 15,
      interview_date: '2026-11-01',
      placed_count: 8,
      created_at: '2026-10-01T10:00:00Z',
    },
  ],
  placed_candidates: [
    {
      id: 'place-001',
      student_id: 'stud-001',
      student_name: 'Aarav Sharma',
      student_roll_number: '1GQ22CS001',
      job_title: 'TCS Ninja & Digital 2026 Drive',
      designation_offered: 'Systems Engineer',
      offered_ctc: 750000.0,
      acceptance_status: 'ACCEPTED',
      joining_status: 'JOINED',
      status_updated_at: '2026-10-20T12:00:00Z',
    },
  ],
};

const mockCompanyTimeline = [
  {
    id: 'evt-001',
    category: 'OUTREACH',
    channel: 'CALL',
    channel_display: 'Phone Call',
    direction: 'OUTBOUND',
    subject: 'Initial 2026 Campus Hiring Discussion',
    summary: 'Discussed schedule with campus hiring head Sunita Rao.',
    actor_name: 'Priya Sharma',
    contact_name: 'Sunita Rao',
    status: 'CONNECTED_INTERESTED',
    timestamp: '2026-09-15T11:00:00Z',
  },
  {
    id: 'evt-002',
    category: 'DISPATCH',
    channel: 'EMAIL',
    channel_display: 'Email',
    direction: 'OUTBOUND',
    subject: 'Candidate Roster & Approved Resumes (45 Candidates)',
    summary: 'Dispatched candidate roster hash a1b2c3d4...',
    actor_name: 'Placement Officer',
    contact_name: 'Sunita Rao',
    status: 'DELIVERED',
    timestamp: '2026-10-05T14:30:00Z',
  },
];

const mockStudent360 = {
  student: {
    id: 'stud-001',
    roll_number: '1GQ22CS001',
    full_name: 'Aarav Sharma',
    institutional_email: 'aarav.cs22@gqt.local',
    department: 'Computer Science',
    degree: 'B.E.',
    college_name: 'GQT Institute of Technology',
    cgpa: 8.75,
    active_backlogs: 0,
    graduation_year: 2026,
    is_verified_by_placement: true,
  },
  readiness_gate: {
    is_certified: true,
    certified_at: '2026-09-20T10:00:00Z',
    comments: 'Candidate meets all Step 23 certification gates.',
  },
  resumes: [
    {
      id: 'res-001',
      version_number: 1,
      file_name: 'aarav_sharma_v1.pdf',
      file_size_bytes: 20480,
      is_current: true,
      created_at: '2026-09-10T12:00:00Z',
    },
  ],
  overall_placement_outcome: 'JOINED',
  placement_history: [
    {
      id: 'ps-001',
      company_name: 'Tata Consultancy Services',
      job_title: 'TCS Ninja & Digital 2026 Drive',
      status: 'SELECTED',
      status_display: 'Selected',
      designation_offered: 'Systems Engineer',
      offered_ctc: 750000.0,
      acceptance_status: 'ACCEPTED',
      joining_status: 'JOINED',
      status_updated_at: '2026-10-20T12:00:00Z',
    },
  ],
  applications: [],
  submissions: [],
  trainer_evaluations: [
    {
      id: 'te-001',
      trainer_name: 'Vikram Joshi',
      student_readiness: 'READY',
      student_readiness_display: 'Ready',
      training_effectiveness_rating: 5,
      areas_for_improvement: 'Focus on distributed systems and microservices architecture.',
      created_at: '2026-09-18T15:00:00Z',
    },
  ],
};

describe('Frontend Phase 10: CRM Database Update Suite', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders CRM Reconciliation Page with 8 health diagnostic cards, health score, and conflicts', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/auth/me/') {
        return { data: mockAdminUser };
      }
      if (url === '/crm/reconciliation/diagnostics/') {
        return { data: { success: true, data: mockDiagnosticsReport } };
      }
      if (url === '/crm/reconciliation/history/') {
        return { data: { success: true, data: mockReconciliationHistory } };
      }
      return { data: {} };
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <CrmReconciliationPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    // Header & Health score
    await waitFor(() => {
      expect(screen.getByText(/CRM Database Reconciliation/i)).toBeInTheDocument();
      expect(screen.getByText(/Cross-Module Platform Health Score/i)).toBeInTheDocument();
      expect(screen.getByText('97.5%')).toBeInTheDocument();
    });

    // 8 Domain Area Cards
    expect(screen.getAllByText('Company').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('HR Contacts').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Students').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Resume Versions').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Interview Status').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Placement Status').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Feedback').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('Communication History').length).toBeGreaterThanOrEqual(1);

    // Conflicts Table
    expect(screen.getByText(/Cross-Module Data Conflicts & Integrity Issues/i)).toBeInTheDocument();
    expect(screen.getByText(/Company 'TCS' has placed candidate records/i)).toBeInTheDocument();
    expect(screen.getByText(/Student '1GQ22CS099' has invalid CGPA/i)).toBeInTheDocument();

    // Audit History Table
    expect(screen.getByText(/Reconciliation Execution Audit Log/i)).toBeInTheDocument();
    expect(screen.getByText(/Promoted 1 verified placement partner companies/i)).toBeInTheDocument();
  });

  it('allows Staff to open reconciliation modal and trigger synchronization', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/auth/me/') {
        return { data: mockAdminUser };
      }
      if (url === '/crm/reconciliation/diagnostics/') {
        return { data: { success: true, data: mockDiagnosticsReport } };
      }
      if (url === '/crm/reconciliation/history/') {
        return { data: { success: true, data: mockReconciliationHistory } };
      }
      return { data: {} };
    });

    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        success: true,
        message: 'CRM database reconciliation completed successfully.',
        data: {
          run_id: 'run-002',
          dry_run: false,
          records_synchronized: 1,
          conflicts_detected: 2,
          health_score_percentage: 97.5,
          diagnostics: mockDiagnosticsReport,
        },
      },
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <CrmReconciliationPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Reconcile Database/i })).toBeInTheDocument();
    });

    // Click Reconcile Database button
    fireEvent.click(screen.getByRole('button', { name: /Reconcile Database/i }));

    // Modal opens
    expect(screen.getByText(/Trigger CRM Database Reconciliation/i)).toBeInTheDocument();
    expect(screen.getByText(/Execute Live Reconciliation/i)).toBeInTheDocument();

    // Click execute
    fireEvent.click(screen.getByRole('button', { name: /Execute Live Reconciliation/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/crm/reconciliation/sync/', { dry_run: false });
    });
  });

  it('renders Auditor read-only badge and restricts reconciliation button for Auditor role', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/auth/me/') {
        return { data: mockAuditorUser };
      }
      if (url === '/crm/reconciliation/diagnostics/') {
        return { data: { success: true, data: mockDiagnosticsReport } };
      }
      if (url === '/crm/reconciliation/history/') {
        return { data: { success: true, data: mockReconciliationHistory } };
      }
      return { data: {} };
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <CrmReconciliationPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Auditor Read-Only/i)).toBeInTheDocument();
      expect(screen.getByText(/Auditor Role Active:/i)).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /^Reconcile Database$/i })).not.toBeInTheDocument();
    });
  });

  it('renders CompanyDetailPage with 360-degree Recruitment Summary and Communication Timeline tabs', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/auth/me/') {
        return { data: mockAdminUser };
      }
      if (url.startsWith('/crm/companies/comp-001/360/')) {
        return { data: { success: true, data: mockCompany360 } };
      }
      if (url.startsWith('/crm/companies/comp-001/timeline/')) {
        return { data: { success: true, data: mockCompanyTimeline } };
      }
      if (url.startsWith('/crm/companies/comp-001/')) {
        return {
          data: {
            ...mockCompany360.company,
            website: 'https://tcs.com',
            source: 'CAMPUS_INBOUND',
            country: 'India',
            address: 'Whitefield Campus, Bengaluru',
            notes: 'Long-standing hiring partner.',
            hr_contacts: mockCompany360.hr_contacts,
            open_follow_ups_count: 0,
            is_archived: false,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        };
      }
      return { data: {} };
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/crm/companies/comp-001']}>
            <Routes>
              <Route path="/crm/companies/:id" element={<CompanyDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    // 360 tab is default
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Recruitment Summary/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Communication Timeline/i })).toBeInTheDocument();
      expect(screen.getByText(/Total Drives/i)).toBeInTheDocument();
      expect(screen.getByText('₹7.50 LPA')).toBeInTheDocument(); // avg offered CTC
      expect(screen.getByText(/Corporate HR Evaluations Summary/i)).toBeInTheDocument();
      expect(screen.getByText(/Placed Candidates/i)).toBeInTheDocument();
      expect(screen.getByText(/Aarav Sharma/i)).toBeInTheDocument();
    });

    // Switch to Communication Timeline tab
    fireEvent.click(screen.getByRole('button', { name: /Communication Timeline/i }));

    await waitFor(() => {
      expect(screen.getByText(/Chronological Communication History/i)).toBeInTheDocument();
      expect(screen.getByText(/Initial 2026 Campus Hiring Discussion/i)).toBeInTheDocument();
      expect(screen.getByText(/Candidate Roster & Approved Resumes/i)).toBeInTheDocument();
    });
  });

  it('renders StudentDirectoryPage and opens 360-degree Candidate Profile modal', async () => {
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url === '/auth/me/') {
        return { data: mockAdminUser };
      }
      if (url.startsWith('/students/profiles/')) {
        return {
          data: [
            {
              id: 'stud-001',
              user_id: 'user-stud-1',
              roll_number: '1GQ22CS001',
              full_name: 'Aarav Sharma',
              institutional_email: 'aarav.cs22@gqt.local',
              department: 'Computer Science',
              degree: 'B.E.',
              college_name: 'GQT Institute of Technology',
              graduation_year: 2026,
              cgpa: '8.75',
              active_backlogs: 0,
              is_verified_by_placement: true,
              current_resume: { id: 'res-001', version_number: 1 },
              created_at: new Date().toISOString(),
              updated_at: new Date().toISOString(),
            },
          ],
        };
      }
      if (url.startsWith('/crm/students/stud-001/360/')) {
        return { data: { success: true, data: mockStudent360 } };
      }
      if (url.startsWith('/crm/students/stud-001/timeline/')) {
        return { data: { success: true, data: [] } };
      }
      return { data: {} };
    });

    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <StudentDirectoryPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('1GQ22CS001')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /360° Profile/i })).toBeInTheDocument();
    });

    // Click 360° Profile button to open modal
    fireEvent.click(screen.getByRole('button', { name: /360° Profile/i }));

    await waitFor(() => {
      expect(screen.getByText(/Resume Version History/i)).toBeInTheDocument();
      expect(screen.getByText(/Version 1: aarav_sharma_v1.pdf/i)).toBeInTheDocument();
      expect(screen.getByText(/Placement & Offer Letter Outcomes/i)).toBeInTheDocument();
      expect(screen.getByText(/Trainer Readiness Evaluations/i)).toBeInTheDocument();
      expect(screen.getByText(/Evaluated by Vikram Joshi/i)).toBeInTheDocument();
    });
  });
});
