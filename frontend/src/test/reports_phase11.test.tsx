import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReportsHubPage } from '../pages/reports/ReportsHubPage';
import { AuthProvider } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
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

const mockCompanyData = {
  summary: {
    total_companies: 15,
    total_job_drives: 24,
    total_submissions: 120,
    total_interviews: 65,
    total_selections: 32,
    total_offers: 30,
    total_joinings: 28,
    overall_selection_rate: 49.23,
    overall_joining_rate: 93.33,
    overall_average_ctc_lakhs: 8.45,
    average_recruiter_rating: 4.6,
  },
  companies: [
    {
      company_id: 'comp-001',
      company_name: 'TechCorp Enterprise Solutions',
      tier: 'TIER_1',
      industry_domain: 'Enterprise Cloud & SaaS',
      drives_count: 3,
      submissions_count: 25,
      interviews_count: 14,
      selections_count: 8,
      offers_count: 8,
      joinings_count: 7,
      min_ctc_lakhs: 8.5,
      max_ctc_lakhs: 14.0,
      avg_ctc_lakhs: 11.25,
      recruiter_satisfaction_rating: 4.8,
      selection_rate: 57.14,
      joining_rate: 87.5,
    },
  ],
};

const mockStudentData = {
  summary: {
    total_students: 250,
    total_verified_academics: 235,
    verification_rate: 94.0,
    total_readiness_certified: 180,
    readiness_certified_rate: 72.0,
    total_applications: 420,
    total_interview_participations: 165,
    total_placed: 145,
    placement_rate: 58.0,
  },
  department_breakdown: [
    {
      department: 'Computer Science and Engineering',
      total_students: 120,
      verified_count: 115,
      certified_count: 95,
      placed_count: 80,
      placement_percentage: 66.67,
    },
    {
      department: 'Electronics and Communication',
      total_students: 80,
      verified_count: 75,
      certified_count: 55,
      placed_count: 45,
      placement_percentage: 56.25,
    },
  ],
  year_breakdown: [
    {
      passing_year: 2026,
      total_students: 180,
      placed_count: 110,
      placement_percentage: 61.11,
    },
    {
      passing_year: 2025,
      total_students: 70,
      placed_count: 35,
      placement_percentage: 50.0,
    },
  ],
  difficulty_distribution: [
    { difficulty_level: 'EASY', rating_count: 12 },
    { difficulty_level: 'MODERATE', rating_count: 48 },
    { difficulty_level: 'DIFFICULT', rating_count: 22 },
    { difficulty_level: 'EXTREME', rating_count: 6 },
  ],
};

const mockPlacementData = {
  summary: {
    total_placement_records: 160,
    total_selected: 145,
    total_rejected: 10,
    total_waiting_list: 3,
    total_hold: 2,
    offers_accepted: 130,
    offers_declined: 8,
    offers_pending: 5,
    offers_expired: 2,
    joining_joined: 125,
    joining_not_joined: 3,
    joining_deferred: 2,
    joining_pending: 0,
    min_ctc_lakhs: 4.5,
    max_ctc_lakhs: 24.0,
    avg_ctc_lakhs: 8.75,
    median_ctc_lakhs: 7.5,
  },
  company_placements: [
    {
      company_name: 'TechCorp Enterprise Solutions',
      total_selected: 8,
      offers_accepted: 8,
      confirmed_joined: 7,
      average_ctc_lakhs: 11.25,
    },
    {
      company_name: 'InnovateX Global',
      total_selected: 12,
      offers_accepted: 10,
      confirmed_joined: 10,
      average_ctc_lakhs: 9.5,
    },
  ],
};

const mockPerformanceData = {
  funnel: {
    stages: [
      { stage_number: 1, stage_name: 'Applications Received', count: 500, conversion_rate_from_prev: 100.0, overall_conversion_rate: 100.0 },
      { stage_number: 2, stage_name: 'Eligible Candidates', count: 420, conversion_rate_from_prev: 84.0, overall_conversion_rate: 84.0 },
      { stage_number: 3, stage_name: 'Readiness Certified (Step 23 Gate)', count: 350, conversion_rate_from_prev: 83.33, overall_conversion_rate: 70.0 },
      { stage_number: 4, stage_name: 'Profiles Dispatched to Corporate HR', count: 320, conversion_rate_from_prev: 91.43, overall_conversion_rate: 64.0 },
      { stage_number: 5, stage_name: 'Corporate Shortlists Received', count: 210, conversion_rate_from_prev: 65.63, overall_conversion_rate: 42.0 },
      { stage_number: 6, stage_name: 'Interviews Conducted', count: 180, conversion_rate_from_prev: 85.71, overall_conversion_rate: 36.0 },
      { stage_number: 7, stage_name: 'Selected Candidates', count: 90, conversion_rate_from_prev: 50.0, overall_conversion_rate: 18.0 },
      { stage_number: 8, stage_name: 'Offers Issued', count: 85, conversion_rate_from_prev: 94.44, overall_conversion_rate: 17.0 },
      { stage_number: 9, stage_name: 'Offers Accepted', count: 78, conversion_rate_from_prev: 91.76, overall_conversion_rate: 15.6 },
      { stage_number: 10, stage_name: 'Candidates Joined', count: 75, conversion_rate_from_prev: 96.15, overall_conversion_rate: 15.0 },
    ],
    total_applications: 500,
    total_joined: 75,
    overall_pipeline_yield: 15.0,
  },
};

const mockMonthlyData = {
  year: 2026,
  month: 10,
  timezone: 'Asia/Kolkata',
  metrics: {
    job_drives_posted: 6,
    submissions_dispatched: 45,
    interviews_conducted: 32,
    results_received: 28,
    candidates_selected: 18,
    offers_accepted: 16,
    joinings_confirmed: 15,
    total_ctc_offered_lakhs: 142.5,
  },
  annual_trend: [
    { month: 1, job_drives_posted: 2, candidates_selected: 5, offers_accepted: 4, joinings_confirmed: 4 },
    { month: 10, job_drives_posted: 6, candidates_selected: 18, offers_accepted: 16, joinings_confirmed: 15 },
  ],
};

const mockStudentSelfData = {
  student_id: 'stud-001',
  usn: '1GQ22CS099',
  full_name: 'Suresh Kumar',
  department: 'Computer Science and Engineering',
  passing_year: 2026,
  profile_completeness_percentage: 95,
  academic_verification_status: 'VERIFIED',
  is_readiness_certified: true,
  total_applications: 8,
  total_shortlists: 4,
  total_interviews: 3,
  placement_result_status: 'SELECTED',
  has_offer: true,
  offer_status: 'ACCEPTED',
  joining_status: 'JOINED',
  offered_ctc_lakhs: 12.5,
};

describe('Phase 11: Reports & Analytics Hub UI Suite', () => {
  let queryClient: QueryClient;

  const setupDefaultMocks = (role: string = 'ADMIN') => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Mock window.URL for CSV export
    window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
    window.URL.revokeObjectURL = vi.fn();

    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-001',
            email: 'admin@gqt.internal',
            full_name: 'Placement Officer',
            roles: [role],
            role_assignments: [{ id: 'ra-1', role: { code: role, name: role }, is_active: true }],
            is_active: true,
            is_staff: role === 'ADMIN' || role === 'PLACEMENT_OFFICER',
            is_superuser: role === 'ADMIN',
          },
        });
      }
      if (url.includes('/reports/company/export/')) {
        return Promise.resolve({ data: new Blob(['Company,Tier\nTest,TIER_1']) });
      }
      if (url.includes('/reports/company/')) {
        return Promise.resolve({ data: mockCompanyData });
      }
      if (url.includes('/reports/students/my-summary/')) {
        return Promise.resolve({ data: mockStudentSelfData });
      }
      if (url.includes('/reports/students/export/')) {
        return Promise.resolve({ data: new Blob(['Department,Total\nCSE,120']) });
      }
      if (url.includes('/reports/students/')) {
        return Promise.resolve({ data: mockStudentData });
      }
      if (url.includes('/reports/placements/export/')) {
        return Promise.resolve({ data: new Blob(['Selected,Offers\n145,130']) });
      }
      if (url.includes('/reports/placements/')) {
        return Promise.resolve({ data: mockPlacementData });
      }
      if (url.includes('/reports/performance/export/')) {
        return Promise.resolve({ data: new Blob(['Stage,Count\n1,500']) });
      }
      if (url.includes('/reports/performance/')) {
        return Promise.resolve({ data: mockPerformanceData });
      }
      if (url.includes('/reports/monthly/export/')) {
        return Promise.resolve({ data: new Blob(['Month,Drives\n10,6']) });
      }
      if (url.includes('/reports/monthly/')) {
        return Promise.resolve({ data: mockMonthlyData });
      }
      return Promise.resolve({ data: {} });
    });
  };

  const renderComponent = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <ReportsHubPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    setupDefaultMocks('ADMIN');
  });

  it('renders Company Reports tab with summary KPIs and corporate hiring table', async () => {
    renderComponent();

    expect(await screen.findByText('Institutional Reports & Analytics Hub')).toBeInTheDocument();
    expect(screen.getByText('1. Company Reports')).toBeInTheDocument();

    // Verify company table data
    expect(await screen.findByText('TechCorp Enterprise Solutions')).toBeInTheDocument();
    expect(screen.getByText('Enterprise Cloud & SaaS')).toBeInTheDocument();
    expect(screen.getByText('TIER_1')).toBeInTheDocument();
    expect(screen.getByText('11.25 LPA')).toBeInTheDocument();
    expect(screen.getByText('★ 4.8')).toBeInTheDocument();
  });

  it('switches to Student Reports tab and renders department breakdown and difficulty perception', async () => {
    renderComponent();

    const studentTabBtn = await screen.findByText('2. Student Reports');
    fireEvent.click(studentTabBtn);

    expect(await screen.findByText('Department-wise Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Computer Science and Engineering')).toBeInTheDocument();
    expect(screen.getByText('Electronics and Communication')).toBeInTheDocument();
    expect(screen.getByText('Passing Year Cohort Distribution')).toBeInTheDocument();
    expect(screen.getByText('Interview Difficulty Perception')).toBeInTheDocument();
    expect(screen.getByText('Candidate Anonymity Preserved')).toBeInTheDocument();
  });

  it('switches to Placement Reports tab and renders Step 36-41 lifecycle metrics and CTC analytics', async () => {
    renderComponent();

    const placementTabBtn = await screen.findByText('3. Placement Reports');
    fireEvent.click(placementTabBtn);

    expect(await screen.findByText('Step 36: Final Result Status')).toBeInTheDocument();
    expect(screen.getByText('Step 38: Offer Letter Lifecycle')).toBeInTheDocument();
    expect(screen.getByText('Step 40: Joining Outcomes')).toBeInTheDocument();
    expect(screen.getByText('Institutional Compensation Analytics (CTC in ₹ Lakhs)')).toBeInTheDocument();
    expect(screen.getByText('Company Placements Table')).toBeInTheDocument();
    expect(screen.getByText('InnovateX Global')).toBeInTheDocument();
  });

  it('switches to Performance Funnel tab and renders 10-stage objective recruitment pipeline', async () => {
    renderComponent();

    const performanceTabBtn = await screen.findByText('4. Performance Funnel');
    fireEvent.click(performanceTabBtn);

    expect(await screen.findByText('Objective 10-Stage Recruitment Conversion Funnel')).toBeInTheDocument();
    expect(screen.getByText('Overall Pipeline Yield')).toBeInTheDocument();
    expect(screen.getAllByText(/15%/).length).toBeGreaterThan(0);
    expect(screen.getByText(/75 Joined \/ 500 Applications/)).toBeInTheDocument();
    expect(screen.getByText('Applications Received')).toBeInTheDocument();
    expect(screen.getByText('Readiness Certified (Step 23 Gate)')).toBeInTheDocument();
    expect(screen.getByText('Profiles Dispatched to Corporate HR')).toBeInTheDocument();
    expect(screen.getByText('Corporate Shortlists Received')).toBeInTheDocument();
    expect(screen.getByText('Candidates Joined')).toBeInTheDocument();
  });

  it('switches to Monthly Statistics tab and displays calendar event breakdown and annual trend', async () => {
    renderComponent();

    const monthlyTabBtn = await screen.findByText('5. Monthly Statistics');
    fireEvent.click(monthlyTabBtn);

    expect(await screen.findByText('Deterministic Timezone:')).toBeInTheDocument();
    expect(screen.getByText('Asia/Kolkata')).toBeInTheDocument();
    expect(screen.getByText('Interviews Conducted')).toBeInTheDocument();
    expect(screen.getByText('Results Received')).toBeInTheDocument();
    expect(screen.getByText(/Annual 12-Month Progression Trend/)).toBeInTheDocument();
  });

  it('triggers secure sanitized CSV download when Export button is clicked', async () => {
    renderComponent();

    const exportBtn = await screen.findByText('Export CSV (Sanitized)');
    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(window.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  it('displays Auditor inspection read-only badge when user role is AUDITOR', async () => {
    setupDefaultMocks('AUDITOR');
    renderComponent();

    expect(
      await screen.findByText('Auditor Inspection Mode — Strict Read-Only')
    ).toBeInTheDocument();
  });

  it('renders isolated Student Self-Report view when user role is STUDENT', async () => {
    setupDefaultMocks('STUDENT');
    renderComponent();

    expect(await screen.findByText('Personal Placement & Readiness Report')).toBeInTheDocument();
    expect(await screen.findByText('Suresh Kumar')).toBeInTheDocument();
    expect(screen.getByText('USN: 1GQ22CS099')).toBeInTheDocument();
    expect(screen.getByText('95%')).toBeInTheDocument();
    expect(screen.getByText('12.5 LPA')).toBeInTheDocument();
    expect(screen.getByText(/Candidate isolation notice:/)).toBeInTheDocument();
  });
});
