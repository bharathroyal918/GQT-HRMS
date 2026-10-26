import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { JobPublicationPage } from '../pages/students/JobPublicationPage';
import { StudentRegistrationPage } from '../pages/students/StudentRegistrationPage';
import { StudentProfileWorkspacePage } from '../pages/students/StudentProfileWorkspacePage';
import { EligibilityWorkspacePage } from '../pages/students/EligibilityWorkspacePage';
import { CandidateCohortPage } from '../pages/students/CandidateCohortPage';
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

const mockJob = {
  id: 'job-101',
  title: 'Associate Software Engineer',
  company: 'comp-101',
  company_name: 'Cognizant Technologies',
  location: 'Bangalore',
  status: 'APPROVED',
  min_cgpa: '7.00',
  registration_deadline: '2026-12-31T23:59:59Z',
  interview_date: '2027-01-15',
  eligibility_criteria: 'CS and IS branches, 7.00 CGPA, 0 backlogs.',
};

const mockProfile = {
  id: 'prof-101',
  user: 'user-101',
  full_name: 'Rahul Sharma',
  email: 'rahul.sharma@gqt.edu',
  roll_number: '1GQT21CS042',
  institutional_email: 'rahul.sharma@gqt.edu',
  college_name: 'GQT Institute of Technology',
  degree: 'B.Tech',
  department: 'Computer Science & Engineering',
  graduation_year: 2025,
  cgpa: '8.45',
  active_backlogs: 0,
  history_backlogs: 0,
  phone_number: '+91 98765 43210',
  alternate_phone: '',
  is_verified_by_placement: true,
  current_resume: {
    id: 'res-1',
    version_number: 1,
    file_name: 'rahul_resume_v1.pdf',
    file_size_bytes: 245760,
    sha256_hash: '3f4b2c1a8e9d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b',
    is_current: true,
    download_url: '/api/v1/students/resumes/res-1/download/',
    uploaded_at: '2026-10-26T10:00:00Z',
  },
  resumes: [
    {
      id: 'res-1',
      version_number: 1,
      file_name: 'rahul_resume_v1.pdf',
      file_size_bytes: 245760,
      sha256_hash: '3f4b2c1a8e9d7c6b5a4f3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b',
      is_current: true,
      download_url: '/api/v1/students/resumes/res-1/download/',
      uploaded_at: '2026-10-26T10:00:00Z',
    },
  ],
  created_at: '2026-10-26T09:00:00Z',
  updated_at: '2026-10-26T10:00:00Z',
};

const mockApplications = [
  {
    id: 'app-1',
    student: 'prof-101',
    student_roll: '1GQT21CS042',
    student_name: 'Rahul Sharma',
    student_department: 'Computer Science & Engineering',
    student_cgpa: '8.45',
    student_active_backlogs: 0,
    student_graduation_year: 2025,
    job_requirement: 'job-101',
    job_title: 'Associate Software Engineer',
    company_name: 'Cognizant Technologies',
    resume_id: 'res-1',
    resume_version: 1,
    status: 'ELIGIBLE',
    status_display: 'Eligible',
    applied_at: '2026-10-26T11:00:00Z',
    eligibility_evaluation: {
      id: 'eval-1',
      status: 'ELIGIBLE',
      status_display: 'Eligible',
      criteria_snapshot: { min_cgpa: '7.00' },
      evaluation_details: [
        {
          criterion: 'Discipline / Branch',
          student_value: 'Computer Science & Engineering',
          required_value: 'CS and IS branches',
          passed: true,
          details: 'Discipline satisfies criteria.',
        },
        {
          criterion: 'Minimum Academic CGPA',
          student_value: '8.45',
          required_value: '>= 7.00',
          passed: true,
          details: 'CGPA meets cutoff.',
        },
      ],
      is_overridden: false,
      override_reason: '',
      override_by: null,
      override_by_name: null,
      override_at: null,
      evaluated_at: '2026-10-26T11:00:00Z',
    },
  },
];

const mockCohort = {
  id: 'cohort-101',
  job_requirement: 'job-101',
  job_title: 'Associate Software Engineer',
  company_name: 'Cognizant Technologies',
  title: 'Candidate Cohort — Associate Software Engineer (Cognizant)',
  is_locked: false,
  finalized_by: null,
  finalized_by_name: null,
  finalized_at: null,
  finalization_notes: '',
  member_count: 1,
  eligible_member_count: 1,
  members: [
    {
      id: 'member-1',
      student_id: 'prof-101',
      student_roll: '1GQT21CS042',
      student_name: 'Rahul Sharma',
      student_email: 'rahul.sharma@gqt.edu',
      student_department: 'Computer Science & Engineering',
      student_cgpa: '8.45',
      student_active_backlogs: 0,
      student_graduation_year: 2025,
      application: 'app-1',
      resume_id: 'res-1',
      resume_version: 1,
      is_eligible: true,
      is_override: false,
      override_reason: '',
      override_by_name: null,
      override_at: null,
      created_at: '2026-10-26T11:30:00Z',
    },
  ],
  created_at: '2026-10-26T11:30:00Z',
  updated_at: '2026-10-26T11:30:00Z',
};

describe('Phase 5: Student Registration & Eligibility Engine Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('renders student registration form with required academic fields', async () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <StudentRegistrationPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    expect(screen.getByText(/GQT Student Registration & Onboarding/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/1GQT21CS042/i)).toBeInTheDocument();
    expect(screen.getByText(/Degree Program/i)).toBeInTheDocument();
    expect(screen.getByText(/Department \/ Branch/i)).toBeInTheDocument();
  });

  it('renders student profile workspace with credentials and resume document vault', async () => {
    const queryClient = createTestQueryClient();
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: mockProfile });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <StudentProfileWorkspacePage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
      expect(screen.getByText('1GQT21CS042')).toBeInTheDocument();
      expect(screen.getByText('8.45')).toBeInTheDocument();
      expect(screen.getByText('rahul_resume_v1.pdf')).toBeInTheDocument();
      expect(screen.getByText(/Active \/ Current/i)).toBeInTheDocument();
    });
  });

  it('renders job publication page and allows channel selection', async () => {
    const queryClient = createTestQueryClient();
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/jobs/requirements/job-101/')) {
        return Promise.resolve({ data: mockJob });
      }
      if (url.includes('/creatives/requests/')) {
        return Promise.resolve({ data: { data: [] } });
      }
      if (url.includes('/students/publications/')) {
        return Promise.resolve({ data: [] });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/jobs/job-101/publish']}>
          <Routes>
            <Route path="/jobs/:id/publish" element={<JobPublicationPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Associate Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('WhatsApp')).toBeInTheDocument();
      expect(screen.getByText('Telegram')).toBeInTheDocument();
      expect(screen.getByText('Email')).toBeInTheDocument();
      expect(screen.getByText('Portal')).toBeInTheDocument();
      expect(screen.getByText(/Dispatch Notification Broadcast/i)).toBeInTheDocument();
    });
  });

  it('renders eligibility workspace with applications and evaluation details', async () => {
    const queryClient = createTestQueryClient();
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/jobs/requirements/job-101/')) {
        return Promise.resolve({ data: mockJob });
      }
      if (url.includes('/students/applications/')) {
        return Promise.resolve({ data: mockApplications });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/jobs/job-101/eligibility']}>
          <Routes>
            <Route path="/jobs/:id/eligibility" element={<EligibilityWorkspacePage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Associate Software Engineer')).toBeInTheDocument();
      expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
      expect(screen.getByText('1GQT21CS042')).toBeInTheDocument();
      expect(screen.getByText('Inspect Details')).toBeInTheDocument();
      expect(screen.getByText('Override')).toBeInTheDocument();
    });

    // Click inspect details to view criterion breakdown
    fireEvent.click(screen.getByText('Inspect Details'));
    expect(screen.getByText(/Criterion-by-Criterion Evaluation Breakdown/i)).toBeInTheDocument();
    expect(screen.getByText('Discipline / Branch')).toBeInTheDocument();
    expect(screen.getByText('Minimum Academic CGPA')).toBeInTheDocument();
  });

  it('renders candidate cohort page and displays verified members', async () => {
    const queryClient = createTestQueryClient();
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url.includes('/auth/users/me/')) {
        return Promise.resolve({
          data: {
            id: 'head-1',
            email: 'head@gqt.edu',
            full_name: 'Placement Head',
            roles: ['PLACEMENT_HEAD'],
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url.includes('/jobs/requirements/job-101/')) {
        return Promise.resolve({ data: mockJob });
      }
      if (url.includes('/students/cohorts/job-101/')) {
        return Promise.resolve({ data: mockCohort });
      }
      return Promise.reject(new Error(`Unhandled URL: ${url}`));
    });

    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/jobs/job-101/cohort']}>
            <Routes>
              <Route path="/jobs/:id/cohort" element={<CandidateCohortPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Candidate Cohort — Associate Software Engineer (Cognizant)')).toBeInTheDocument();
      expect(screen.getByText('1GQT21CS042')).toBeInTheDocument();
      expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
      expect(screen.getByText(/Automated Engine/i)).toBeInTheDocument();
      expect(screen.getByText(/Finalize & Lock Cohort/i)).toBeInTheDocument();
    });
  });

  it('renders student directory page with registered candidates', async () => {
    const queryClient = createTestQueryClient();
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: [mockProfile] });

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <StudentDirectoryPage />
        </MemoryRouter>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Student Talent Directory')).toBeInTheDocument();
      expect(screen.getByText('1GQT21CS042')).toBeInTheDocument();
      expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
      expect(screen.getByText('Verified')).toBeInTheDocument();
    });
  });
});
