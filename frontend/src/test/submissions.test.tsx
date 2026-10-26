import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CandidateSubmissionWorkspacePage } from '../pages/submissions/CandidateSubmissionWorkspacePage';
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

const mockPackages = [
  {
    id: 'pkg-001',
    title: 'Infosys Technologies - ASE 2026 Cohort 1',
    job_id: 'job-001',
    job_title: 'Associate Software Engineer',
    company_id: 'comp-001',
    company_name: 'Infosys Technologies',
    hr_contact_id: 'hr-001',
    hr_contact_name: 'Pooja Sharma',
    status: 'READY_FOR_DISPATCH',
    candidate_count: 2,
    package_hash: 'a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2',
    roster_file_name: 'GQT_Infosys_ASE_Roster.xlsx',
    has_roster_file: true,
    created_at: '2026-10-26T10:00:00Z',
    dispatched_at: null,
    acknowledged_at: null,
    created_by_name: 'Placement Officer',
    dispatched_by_name: null,
  },
  {
    id: 'pkg-002',
    title: 'TCS - Prime Developer Profiles',
    job_id: 'job-002',
    job_title: 'Software Developer',
    company_id: 'comp-002',
    company_name: 'Tata Consultancy Services',
    hr_contact_id: 'hr-002',
    hr_contact_name: 'Anil Verma',
    status: 'DISPATCHED',
    candidate_count: 3,
    package_hash: 'f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3b2a1f6e5',
    roster_file_name: 'GQT_TCS_Developer_Roster.xlsx',
    has_roster_file: true,
    created_at: '2026-10-25T14:00:00Z',
    dispatched_at: '2026-10-25T15:30:00Z',
    acknowledged_at: null,
    created_by_name: 'Placement Head',
    dispatched_by_name: 'Placement Head',
  },
];

const mockPackageDetail = {
  ...mockPackages[0],
  hr_contact_email: 'pooja.sharma@infosys.example.com',
  hr_contact_phone: '+919876543210',
  roster_download_url: '/api/v1/submissions/packages/pkg-001/roster/download/',
  roster_generated_at: '2026-10-26T10:05:00Z',
  resumes_attached_at: '2026-10-26T10:10:00Z',
  notes: 'High readiness candidate roster.',
  dispatch_channel: 'EMAIL',
  recipient_email: 'pooja.sharma@infosys.example.com',
  recipient_name: 'Pooja Sharma',
  recipient_phone: '+919876543210',
  provider_reference: '',
  dispatch_notes: '',
  acknowledged_by_name: null,
  acknowledged_by_contact_name: '',
  acknowledgement_channel: 'EMAIL',
  recruiter_feedback: '',
  tentative_interview_date: null,
  follow_up_callback_date: null,
  candidates: [
    {
      id: 'cs-001',
      student_id: 'stud-001',
      roll_number: '1GQ21CS101',
      student_name: 'Aditi Rao',
      institutional_email: 'aditi.rao@gqt.edu',
      phone_number: '+919876543210',
      department: 'Computer Science',
      graduation_year: 2025,
      cgpa: 8.85,
      resume_id: 'res-001',
      resume_version_number: 1,
      resume_sha256: 'digest111',
      resume_file_url: '/api/v1/students/resumes/res-001/download/',
      status: 'PENDING',
      candidate_snapshot: {},
      created_at: '2026-10-26T10:00:00Z',
      updated_at: '2026-10-26T10:00:00Z',
    },
  ],
  dispatch_logs: [],
};

const mockDispatchedDetail = {
  ...mockPackages[1],
  hr_contact_email: 'anil.verma@tcs.example.com',
  hr_contact_phone: '+919888877777',
  roster_download_url: '/api/v1/submissions/packages/pkg-002/roster/download/',
  roster_generated_at: '2026-10-25T14:05:00Z',
  resumes_attached_at: '2026-10-25T14:10:00Z',
  notes: 'TCS Drive submissions.',
  dispatch_channel: 'EMAIL',
  recipient_email: 'anil.verma@tcs.example.com',
  recipient_name: 'Anil Verma',
  recipient_phone: '+919888877777',
  provider_reference: 'MSG-DISP-ABC123XYZ',
  dispatch_notes: 'Profiles dispatched.',
  acknowledged_by_name: null,
  acknowledged_by_contact_name: '',
  acknowledgement_channel: 'EMAIL',
  recruiter_feedback: '',
  tentative_interview_date: null,
  follow_up_callback_date: null,
  candidates: [
    {
      id: 'cs-002',
      student_id: 'stud-002',
      roll_number: '1GQ21CS102',
      student_name: 'Rahul Sharma',
      institutional_email: 'rahul.s@gqt.edu',
      phone_number: '+919888877777',
      department: 'Information Science',
      graduation_year: 2025,
      cgpa: 8.20,
      resume_id: 'res-002',
      resume_version_number: 2,
      resume_sha256: 'digest222',
      resume_file_url: '/api/v1/students/resumes/res-002/download/',
      status: 'SUBMITTED',
      candidate_snapshot: {},
      created_at: '2026-10-25T14:00:00Z',
      updated_at: '2026-10-25T15:30:00Z',
    },
  ],
  dispatch_logs: [
    {
      id: 'log-001',
      attempt_number: 1,
      channel: 'EMAIL',
      recipient: 'anil.verma@tcs.example.com',
      status: 'SENT',
      provider_message_id: 'MSG-DISP-ABC123XYZ',
      response_payload: {},
      dispatched_by_name: 'Placement Head',
      timestamp: '2026-10-25T15:30:00Z',
    },
  ],
};

const mockEligibleCandidatesResponse = {
  job_id: 'job-001',
  job_title: 'Associate Software Engineer',
  company_name: 'Infosys Technologies',
  hr_contact_name: 'Pooja Sharma',
  hr_contact_email: 'pooja.sharma@infosys.example.com',
  total_eligible: 2,
  total_certified: 1,
  candidates: [
    {
      student_id: 'stud-001',
      student_name: 'Aditi Rao',
      roll_number: '1GQ21CS101',
      institutional_email: 'aditi.rao@gqt.edu',
      phone_number: '+919876543210',
      college_name: 'GQT Engineering College',
      department: 'Computer Science',
      graduation_year: 2025,
      cgpa: 8.85,
      technical_skills: 'Java, Python, SQL',
      application_id: 'app-001',
      application_status: 'ELIGIBLE',
      is_in_locked_cohort: true,
      has_readiness_certification: true,
      certification_id: 'cert-001',
      approved_resume_id: 'res-001',
      approved_resume_version: 1,
      approved_resume_file_name: 'resume_v1.pdf',
      approved_resume_sha256: 'digest111',
      is_already_submitted: false,
      can_be_submitted: true,
    },
    {
      student_id: 'stud-002',
      student_name: 'Uncertified Candidate',
      roll_number: '1GQ21CS102',
      institutional_email: 'uncertified@gqt.edu',
      phone_number: '+919876543211',
      college_name: 'GQT Engineering College',
      department: 'Information Science',
      graduation_year: 2025,
      cgpa: 7.50,
      technical_skills: 'Python',
      application_id: 'app-002',
      application_status: 'ELIGIBLE',
      is_in_locked_cohort: true,
      has_readiness_certification: false,
      certification_id: null,
      approved_resume_id: null,
      approved_resume_version: null,
      approved_resume_file_name: null,
      approved_resume_sha256: null,
      is_already_submitted: false,
      can_be_submitted: false,
    },
  ],
};

describe('Frontend Candidate Submissions Suite (Phase 7 / Steps 24-28)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Default API mock handlers
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-head',
            email: 'head@gqt.internal',
            full_name: 'Placement Head Officer',
            role_assignments: [
              { id: 'ra-1', role: { code: 'PLACEMENT_HEAD', name: 'Placement Head' }, is_active: true },
              { id: 'ra-2', role: { code: 'ADMIN', name: 'System Administrator' }, is_active: true },
            ],
            is_staff: true,
            is_superuser: true,
          },
        });
      }
      if (url.includes('/submissions/packages/pkg-001/')) {
        return Promise.resolve({ data: mockPackageDetail });
      }
      if (url.includes('/submissions/packages/pkg-002/')) {
        return Promise.resolve({ data: mockDispatchedDetail });
      }
      if (url.includes('/submissions/packages/')) {
        return Promise.resolve({ data: mockPackages });
      }
      if (url.includes('/submissions/jobs/job-001/candidates/')) {
        return Promise.resolve({ data: mockEligibleCandidatesResponse });
      }
      if (url.includes('/jobs/requirements/')) {
        return Promise.resolve({
          data: {
            success: true,
            data: [
              {
                id: 'job-001',
                title: 'Associate Software Engineer',
                company_name: 'Infosys Technologies',
                status: 'APPROVED',
              },
            ],
          },
        });
      }
      return Promise.resolve({ data: [] });
    });

    (apiClient.post as any).mockImplementation((url: string, payload: any) => {
      if (url.includes('/submissions/packages/')) {
        return Promise.resolve({
          data: {
            ...mockPackageDetail,
            id: 'pkg-new',
            title: payload?.title || 'New Package',
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
  });

  it('renders CandidateSubmissionWorkspacePage with KPI cards and package directory', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/submissions']}>
            <CandidateSubmissionWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Candidate Submissions & Profile Dispatch')).toBeInTheDocument();
      expect(screen.getByText('Total Packages')).toBeInTheDocument();
      expect(screen.getByText('Ready for Dispatch')).toBeInTheDocument();
      expect(screen.getByText('Dispatched to HR')).toBeInTheDocument();
      expect(screen.getByText('Acknowledged by HR')).toBeInTheDocument();
      expect(screen.getAllByText('Infosys Technologies - ASE 2026 Cohort 1')[0]).toBeInTheDocument();
    });
  });

  it('renders candidate roster table and action buttons for selected package', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/submissions']}>
            <CandidateSubmissionWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
      expect(screen.getByText('1GQ21CS101')).toBeInTheDocument();
      expect(screen.getByText('v1')).toBeInTheDocument();
      expect(screen.getByText('SHA-256 Roster Digest:')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Step 27: Send Profiles to HR/i })).toBeInTheDocument();
    });
  });

  it('opens Create Submission Package modal and displays Step 23 readiness badges on candidates', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/submissions']}>
            <CandidateSubmissionWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Create Submission Package/i })).toBeInTheDocument();
    });

    // Click Create Submission Package
    fireEvent.click(screen.getByRole('button', { name: /Create Submission Package/i }));

    expect(screen.getByText('Prepare Candidate List & Assemble Package')).toBeInTheDocument();
    expect(screen.getByText('Target Approved Job Requirement *')).toBeInTheDocument();

    // Wait for approved jobs dropdown options to populate
    await waitFor(() => {
      expect(screen.getByText(/Infosys Technologies — Associate Software Engineer/i)).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'job-001' } });

    await waitFor(() => {
      expect(screen.getByText('Candidate Readiness Pool (2)')).toBeInTheDocument();
      expect(screen.getByText('Placement Ready (v1)')).toBeInTheDocument();
      expect(screen.getByText('Readiness Pending')).toBeInTheDocument();
    });
  });

  it('opens Profile Dispatch modal on button click (Step 27)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/submissions']}>
            <CandidateSubmissionWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Step 27: Send Profiles to HR/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Step 27: Send Profiles to HR/i }));

    expect(screen.getByText('Send Candidate Profiles to HR')).toBeInTheDocument();
    expect(screen.getByText('Transmission Channel')).toBeInTheDocument();
    expect(screen.getByText('Confirm Profile Dispatch')).toBeInTheDocument();
  });

  it('opens Recruiter Acknowledgment modal when viewing a dispatched package (Step 28)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/submissions']}>
            <CandidateSubmissionWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('TCS - Prime Developer Profiles')).toBeInTheDocument();
    });

    // Click dispatched package
    fireEvent.click(screen.getByText('TCS - Prime Developer Profiles'));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Step 28: Record HR Acknowledgement/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Step 28: Record HR Acknowledgement/i }));

    expect(screen.getByText('Log Corporate Recruiter Receipt')).toBeInTheDocument();
    expect(screen.getByText('Recruiter Contact Representative *')).toBeInTheDocument();
    expect(screen.getByText('Tentative Interview Date')).toBeInTheDocument();
    expect(screen.getByText('Follow-Up Callback Date')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Record Recruiter Acknowledgment/i })).toBeInTheDocument();
  });
});
