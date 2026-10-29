import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StudentDrivesPage } from '../pages/students/StudentDrivesPage';
import { studentsApi } from '../api/studentsApi';
import { JobPublication, StudentApplication, StudentProfile } from '../types/students';

let currentMockAuthUser: any = {
  id: 'user-001',
  email: 'aditi.sharma@gqt.edu',
  full_name: 'Aditi Sharma',
  roles: ['STUDENT'],
};

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: currentMockAuthUser,
    isAuthenticated: !!currentMockAuthUser,
    isLoading: false,
    hasRole: (role: string) => currentMockAuthUser?.roles?.includes(role) ?? false,
    hasAnyRole: (roles: string[]) => roles.some((r: string) => currentMockAuthUser?.roles?.includes(r)) ?? false,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

vi.mock('../api/studentsApi', () => ({
  studentsApi: {
    listPublications: vi.fn(),
    listEligiblePublications: vi.fn(),
    listApplications: vi.fn(),
    getProfileMe: vi.fn(),
    applyForJob: vi.fn(),
    previewEligibility: vi.fn(),
    getEligibilityEvaluation: vi.fn(),
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

const mockProfileWithResume: StudentProfile = {
  id: 'prof-001',
  user: 'user-001',
  full_name: 'Aditi Sharma',
  email: 'aditi.sharma@gqt.edu',
  roll_number: '1GQT21CS001',
  institutional_email: 'aditi.sharma@gqt.edu',
  college_name: 'GQT Institute of Technology',
  degree: 'B.Tech',
  department: 'Computer Science',
  graduation_year: 2025,
  cgpa: '8.75',
  active_backlogs: 0,
  history_backlogs: 0,
  phone_number: '+91 98765 11111',
  alternate_phone: '',
  is_verified_by_placement: true,
  current_resume: {
    id: 'res-001',
    version_number: 1,
    file_name: 'aditi_resume_v1.pdf',
    file_size_bytes: 204800,
    sha256_hash: 'abc123hash',
    is_current: true,
    download_url: '/api/v1/students/resumes/res-001/download/',
    uploaded_at: '2026-10-25T10:00:00Z',
  },
  resumes: [],
  created_at: '2026-10-20T10:00:00Z',
  updated_at: '2026-10-25T10:00:00Z',
};

const mockProfileWithoutResume: StudentProfile = {
  ...mockProfileWithResume,
  current_resume: null,
};

const mockPublications: JobPublication[] = [
  {
    id: 'pub-001',
    job_requirement: 'job-001',
    job_title: 'Software Development Engineer',
    company_name: 'Amazon Web Services',
    creative_version: null,
    channel: 'PORTAL',
    channel_display: 'Portal Noticeboard',
    status: 'DELIVERED',
    status_display: 'Delivered',
    target_audience: '2025 Passing Out Batch — CS & IS',
    subject: 'Campus Drive Notice: SDE Role at Amazon',
    message_body: 'Detailed announcement text for AWS campus recruitment drive.',
    dispatched_at: '2026-10-28T09:00:00Z',
    delivered_at: '2026-10-28T09:00:00Z',
    failure_reason: '',
    retry_count: 0,
    provider_message_id: 'msg-001',
    published_by: 'officer-001',
    published_by_name: 'Placement Officer',
    created_at: '2026-10-28T09:00:00Z',
    updated_at: '2026-10-28T09:00:00Z',
    location: 'Bangalore / Hyderabad',
    employment_type: 'FULL_TIME',
    employment_type_display: 'Full-Time Employment',
    min_salary: '1200000.00',
    max_salary: '1600000.00',
    salary_currency: 'INR',
    registration_deadline: '2026-12-31T23:59:59Z',
    interview_date: '2027-01-10',
    eligibility_criteria: 'CS & IS branches. Minimum 7.50 CGPA with zero standing arrears.',
    min_cgpa: '7.50',
    skills_required: 'Data Structures, Algorithms, Java/Python, System Design',
    job_description: 'Design and develop highly scalable cloud infrastructure systems.',
    openings_count: 10,
    has_bond: false,
    bond_details: '',
    eligibility_preview: {
      status: 'ELIGIBLE',
      status_display: 'Eligible',
      passed: true,
      details: [
        {
          criterion: 'Discipline / Branch',
          student_value: 'Computer Science',
          required_value: 'CS & IS',
          passed: true,
          details: 'Department matches required candidate branches.',
        },
        {
          criterion: 'Minimum Academic CGPA',
          student_value: '8.75',
          required_value: '>= 7.50',
          passed: true,
          details: 'Student CGPA satisfies requirement.',
        },
        {
          criterion: 'Active Arrears / Backlogs',
          student_value: '0',
          required_value: '<= 0 active backlog(s)',
          passed: true,
          details: 'Student has zero active backlogs.',
        },
        {
          criterion: 'Graduation Passing Batch',
          student_value: '2025',
          required_value: '2025',
          passed: true,
          details: 'Batch matches targeted recruitment cohort.',
        },
      ],
      criteria_snapshot: { min_cgpa: '7.50' },
    },
  },
  {
    id: 'pub-002',
    job_requirement: 'job-002',
    job_title: 'Graduate Trainee Engineer',
    company_name: 'Tata Consultancy Services',
    creative_version: null,
    channel: 'PORTAL',
    channel_display: 'Portal Noticeboard',
    status: 'DELIVERED',
    status_display: 'Delivered',
    target_audience: 'All B.Tech Circuit Branches',
    subject: 'National Qualifier Test — TCS Drive Notice',
    message_body: 'TCS campus drive details and registration schedule.',
    dispatched_at: '2026-10-27T09:00:00Z',
    delivered_at: '2026-10-27T09:00:00Z',
    failure_reason: '',
    retry_count: 0,
    provider_message_id: 'msg-002',
    published_by: 'officer-001',
    published_by_name: 'Placement Officer',
    created_at: '2026-10-27T09:00:00Z',
    updated_at: '2026-10-27T09:00:00Z',
    location: 'Chennai',
    employment_type: 'FULL_TIME',
    employment_type_display: 'Full-Time Employment',
    min_salary: '400000.00',
    max_salary: '700000.00',
    salary_currency: 'INR',
    // Expired registration deadline to test closed drive state
    registration_deadline: '2026-10-01T00:00:00Z',
    eligibility_criteria: 'All branches, 6.00 CGPA, max 1 backlog allowed.',
    min_cgpa: '6.00',
    skills_required: 'C++, Java, DBMS',
    job_description: 'Enterprise IT services and digital transformation projects.',
    openings_count: 50,
    eligibility_preview: {
      status: 'ELIGIBLE',
      status_display: 'Eligible',
      passed: true,
      details: [
        {
          criterion: 'Minimum Academic CGPA',
          student_value: '8.75',
          required_value: '>= 6.00',
          passed: true,
          details: 'Student CGPA satisfies requirement.',
        },
      ],
      criteria_snapshot: { min_cgpa: '6.00' },
    },
  },
  {
    id: 'pub-003',
    job_requirement: 'job-003',
    job_title: 'Quant Research Engineer',
    company_name: 'Goldman Sachs',
    creative_version: null,
    channel: 'PORTAL',
    channel_display: 'Portal Noticeboard',
    status: 'DELIVERED',
    status_display: 'Delivered',
    target_audience: 'High Honors CGPA >= 9.50',
    subject: 'Quant Research Fellowship',
    message_body: 'Quantitative engineering opportunities.',
    dispatched_at: '2026-10-28T12:00:00Z',
    delivered_at: '2026-10-28T12:00:00Z',
    failure_reason: '',
    retry_count: 0,
    provider_message_id: 'msg-003',
    published_by: 'officer-001',
    published_by_name: 'Placement Officer',
    created_at: '2026-10-28T12:00:00Z',
    updated_at: '2026-10-28T12:00:00Z',
    location: 'Bangalore',
    employment_type: 'FULL_TIME',
    employment_type_display: 'Full-Time Employment',
    min_salary: '2500000.00',
    max_salary: '3500000.00',
    salary_currency: 'INR',
    registration_deadline: '2026-12-31T23:59:59Z',
    eligibility_criteria: 'Min 9.50 CGPA strictly required.',
    min_cgpa: '9.50',
    skills_required: 'C++, Probability, Linear Algebra',
    job_description: 'Algorithmic trading engine development.',
    openings_count: 2,
    eligibility_preview: {
      status: 'INELIGIBLE',
      status_display: 'Ineligible',
      passed: false,
      details: [
        {
          criterion: 'Minimum Academic CGPA',
          student_value: '8.75',
          required_value: '>= 9.50',
          passed: false,
          details: 'Student CGPA 8.75 is below the required 9.50 minimum.',
        },
      ],
      criteria_snapshot: { min_cgpa: '9.50' },
    },
  },
];

const mockAppliedApplication: StudentApplication = {
  id: 'app-001',
  student: 'prof-001',
  student_roll: '1GQT21CS001',
  student_name: 'Aditi Sharma',
  student_department: 'Computer Science',
  student_cgpa: '8.75',
  student_active_backlogs: 0,
  student_graduation_year: 2025,
  job_requirement: 'job-001',
  job_title: 'Software Development Engineer',
  company_name: 'Amazon Web Services',
  resume: 'res-001',
  resume_id: 'res-001',
  resume_version: 1,
  status: 'ELIGIBLE',
  status_display: 'Eligible',
  applied_at: '2026-10-28T10:00:00Z',
  eligibility_evaluation: {
    id: 'eval-001',
    status: 'ELIGIBLE',
    status_display: 'Eligible',
    criteria_snapshot: { min_cgpa: '7.50' },
    evaluation_details: [
      {
        criterion: 'Discipline / Branch',
        student_value: 'Computer Science',
        required_value: 'CS & IS',
        passed: true,
        details: 'Department matches required candidate branches.',
      },
      {
        criterion: 'Minimum Academic CGPA',
        student_value: '8.75',
        required_value: '>= 7.50',
        passed: true,
        details: 'Student CGPA satisfies requirement.',
      },
      {
        criterion: 'Active Arrears / Backlogs',
        student_value: '0',
        required_value: '<= 0 active backlog(s)',
        passed: true,
        details: 'Student has zero active backlogs.',
      },
      {
        criterion: 'Graduation Passing Batch',
        student_value: '2025',
        required_value: '2025',
        passed: true,
        details: 'Batch matches targeted recruitment cohort.',
      },
    ],
    is_overridden: false,
    override_reason: '',
    override_by: null,
    override_by_name: null,
    override_at: null,
    evaluated_at: '2026-10-28T10:00:00Z',
  },
};

describe('StudentDrivesPage — Phase 15 Workstream 1 Verification', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();
    currentMockAuthUser = {
      id: 'user-001',
      email: 'aditi.sharma@gqt.edu',
      full_name: 'Aditi Sharma',
      roles: ['STUDENT'],
    };
  });

  const renderComponent = (initialEntries = ['/students/drives']) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/students/drives" element={<StudentDrivesPage />} />
            <Route path="/access-denied" element={<div data-testid="access-denied-page">Access Denied Page</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders loading state initially while queries are in flight', () => {
    vi.mocked(studentsApi.listPublications).mockReturnValue(new Promise(() => {}));
    vi.mocked(studentsApi.listApplications).mockReturnValue(new Promise(() => {}));
    vi.mocked(studentsApi.getProfileMe).mockReturnValue(new Promise(() => {}));

    renderComponent();
    expect(screen.getByText(/Loading corporate placement drives/i)).toBeInTheDocument();
  });

  it('renders error state with retry button when publication API fails', async () => {
    vi.mocked(studentsApi.listPublications).mockRejectedValue(new Error('Network failure'));
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Unable to load Placement Drives/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });
  });

  it('renders published recruitment opportunities from API data', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
      expect(screen.getByText('Amazon Web Services')).toBeInTheDocument();
      expect(screen.getByText('Graduate Trainee Engineer')).toBeInTheDocument();
      expect(screen.getByText('Tata Consultancy Services')).toBeInTheDocument();
    });

    // Check compensation and location display
    expect(screen.getByText(/INR 1200000.00 - 1600000.00/i)).toBeInTheDocument();
    expect(screen.getByText(/Bangalore \/ Hyderabad/i)).toBeInTheDocument();
  });

  it('displays closed opportunity status when deadline has passed', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Graduate Trainee Engineer')).toBeInTheDocument();
    });

    // TCS deadline is in the past
    expect(screen.getAllByText('Registration Closed').length).toBeGreaterThanOrEqual(1);
    const closedButton = screen.getByRole('button', { name: 'Registration Closed' });
    expect(closedButton).toBeDisabled();
  });

  it('displays already-applied status and eligibility breakdown when student has applied', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([mockAppliedApplication]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Eligible — Meets Criteria')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /View Eligibility Breakdown/i })).toBeInTheDocument();
    });

    // Click to view criterion-by-criterion breakdown
    fireEvent.click(screen.getByRole('button', { name: /View Eligibility Breakdown/i }));

    expect(screen.getByText('Eligibility Engine Evaluation Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Discipline / Branch')).toBeInTheDocument();
    expect(screen.getByText('Department matches required candidate branches.')).toBeInTheDocument();
    expect(screen.getByText('Minimum Academic CGPA')).toBeInTheDocument();
    expect(screen.getByText('Student CGPA satisfies requirement.')).toBeInTheDocument();
  });

  it('filters opportunities by search query input', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/Search placement drives/i);
    fireEvent.change(searchInput, { target: { value: 'Amazon' } });

    expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    expect(screen.queryByText('Graduate Trainee Engineer')).not.toBeInTheDocument();
  });

  it('displays empty state when search matches no opportunities', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/Search placement drives/i);
    fireEvent.change(searchInput, { target: { value: 'NonexistentRoleXYZ' } });

    expect(screen.getByText('No Opportunities Match Your Filter')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Reset Filters/i })).toBeInTheDocument();
  });

  it('displays warning and disables Apply when student has no active resume', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithoutResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText(/Resume Required for Applications/i)).toBeInTheDocument();
    });

    const applyButtons = screen.getAllByRole('button', { name: /Apply for Opportunity/i });
    expect(applyButtons.length).toBeGreaterThanOrEqual(1);
    applyButtons.forEach((btn) => expect(btn).toBeDisabled());
  });

  it('submits drive application and prevents duplicate clicks during submission', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue([mockPublications[0]!]);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    // Controlled promise to inspect pending state
    let resolveApply: (value: StudentApplication) => void;
    const applyPromise = new Promise<StudentApplication>((resolve) => {
      resolveApply = resolve;
    });
    vi.mocked(studentsApi.applyForJob).mockReturnValue(applyPromise);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Apply for Opportunity/i })).toBeInTheDocument();
    });

    // 1. Open confirmation modal
    fireEvent.click(screen.getByRole('button', { name: /Apply for Opportunity/i }));
    expect(screen.getByText('Confirm Drive Application')).toBeInTheDocument();
    expect(screen.getByText('Aditi Sharma (1GQT21CS001)')).toBeInTheDocument();

    // 2. Click confirm
    const confirmButton = screen.getByRole('button', { name: /Confirm & Apply/i });
    fireEvent.click(confirmButton);

    // Verify submission is in progress and button is disabled to prevent duplicate clicks
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Verifying & Submitting/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Verifying & Submitting/i })).toBeDisabled();
    });
    expect(studentsApi.applyForJob).toHaveBeenCalledTimes(1);
    expect(studentsApi.applyForJob).toHaveBeenCalledWith('job-001');

    // 3. Resolve the API call
    resolveApply!(mockAppliedApplication);

    await waitFor(() => {
      expect(screen.getByText(/Application submitted successfully/i)).toBeInTheDocument();
    });
  });

  it('displays validation error alert when server rejects application', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue([mockPublications[0]!]);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);
    vi.mocked(studentsApi.applyForJob).mockRejectedValue({
      response: {
        data: {
          detail: 'You have already submitted an application for this placement opportunity.',
        },
      },
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Apply for Opportunity/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Apply for Opportunity/i }));
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Apply/i }));

    await waitFor(() => {
      expect(
        screen.getByText('You have already submitted an application for this placement opportunity.')
      ).toBeInTheDocument();
    });
  });

  it('redirects ADMIN-only staff account to /access-denied and suppresses student queries (FINDING-WS1-01)', async () => {
    currentMockAuthUser = {
      id: 'admin-001',
      email: 'admin@gqt.edu',
      full_name: 'Placement Administrator',
      roles: ['ADMIN'],
    };

    renderComponent();

    await waitFor(() => {
      expect(screen.getByTestId('access-denied-page')).toBeInTheDocument();
    });

    // Verify zero student API queries dispatched by staff without StudentProfile
    expect(studentsApi.listPublications).not.toHaveBeenCalled();
    expect(studentsApi.listApplications).not.toHaveBeenCalled();
    expect(studentsApi.getProfileMe).not.toHaveBeenCalled();
  });

  it('permits dual-role user (STUDENT and ADMIN) to view opportunities and executes queries', async () => {
    currentMockAuthUser = {
      id: 'dual-001',
      email: 'student.admin@gqt.edu',
      full_name: 'Student Administrator',
      roles: ['STUDENT', 'ADMIN'],
    };

    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
      expect(screen.getByText('Amazon Web Services')).toBeInTheDocument();
    });

    expect(studentsApi.listPublications).toHaveBeenCalledTimes(1);
    expect(studentsApi.getProfileMe).toHaveBeenCalledTimes(1);
  });

  it('displays eligible unapplied opportunities in the Eligible tab (WS1-03 discovery)', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
      expect(screen.getByText('Quant Research Engineer')).toBeInTheDocument();
    });

    // Switch to 'Eligible' filter tab
    const eligibleTab = screen.getByRole('tab', { name: 'Eligible' });
    fireEvent.click(eligibleTab);

    // AWS (eligible preview) should be present
    expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    expect(screen.getAllByText('Eligible to Apply (Preview)').length).toBeGreaterThanOrEqual(1);

    // Goldman Sachs (ineligible preview) should be excluded from Eligible tab
    expect(screen.queryByText('Quant Research Engineer')).not.toBeInTheDocument();
  });

  it('displays ineligible unapplied opportunities in the Ineligible tab', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
      expect(screen.getByText('Quant Research Engineer')).toBeInTheDocument();
    });

    // Switch to 'Ineligible' filter tab
    const ineligibleTab = screen.getByRole('tab', { name: 'Ineligible' });
    fireEvent.click(ineligibleTab);

    // Goldman Sachs (ineligible preview) should be present
    expect(screen.getByText('Quant Research Engineer')).toBeInTheDocument();
    expect(screen.getByText('Ineligible (Preview)')).toBeInTheDocument();

    // AWS (eligible) should be excluded from Ineligible tab
    expect(screen.queryByText('Software Development Engineer')).not.toBeInTheDocument();
  });

  it('opens pre-application eligibility preview modal without submitting an application', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue(mockPublications);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    });

    // Click "View Eligibility Preview" button
    const previewButtons = screen.getAllByRole('button', { name: /View Eligibility Preview/i });
    expect(previewButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(previewButtons[0]!);

    // Modal appears with deterministic breakdown and disclaimer
    expect(screen.getByText('Pre-Application Eligibility Preview')).toBeInTheDocument();
    expect(screen.getByText('Pre-Application Deterministic Evaluation')).toBeInTheDocument();
    expect(screen.getByText('Discipline / Branch')).toBeInTheDocument();

    // Verify apply was NOT called just by previewing
    expect(studentsApi.applyForJob).not.toHaveBeenCalled();

    // Close preview modal
    fireEvent.click(screen.getByRole('button', { name: 'Close Preview' }));
    expect(screen.queryByText('Pre-Application Eligibility Preview')).not.toBeInTheDocument();
  });

  it('permits navigating from pre-application preview modal directly to application modal', async () => {
    vi.mocked(studentsApi.listPublications).mockResolvedValue([mockPublications[0]!]);
    vi.mocked(studentsApi.listApplications).mockResolvedValue([]);
    vi.mocked(studentsApi.getProfileMe).mockResolvedValue(mockProfileWithResume);
    vi.mocked(studentsApi.applyForJob).mockResolvedValue(mockAppliedApplication);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Software Development Engineer')).toBeInTheDocument();
    });

    // 1. Open preview modal
    fireEvent.click(screen.getByRole('button', { name: /View Eligibility Preview/i }));
    expect(screen.getByText('Pre-Application Eligibility Preview')).toBeInTheDocument();

    // 2. Click "Proceed to Apply"
    const proceedButton = screen.getByRole('button', { name: /Proceed to Apply/i });
    fireEvent.click(proceedButton);

    // 3. Application confirmation modal opens
    expect(screen.getByText('Confirm Drive Application')).toBeInTheDocument();

    // 4. Submit application
    fireEvent.click(screen.getByRole('button', { name: /Confirm & Apply/i }));

    await waitFor(() => {
      expect(studentsApi.applyForJob).toHaveBeenCalledTimes(1);
      expect(studentsApi.applyForJob).toHaveBeenCalledWith('job-001');
    });
  });
});
