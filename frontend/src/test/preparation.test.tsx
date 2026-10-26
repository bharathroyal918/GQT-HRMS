import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ResumeReviewWorkspacePage } from '../pages/preparation/ResumeReviewWorkspacePage';
import { StudentAssessmentsPage } from '../pages/preparation/StudentAssessmentsPage';
import { MockInterviewWorkspacePage } from '../pages/preparation/MockInterviewWorkspacePage';
import { PlacementReadinessGatePage } from '../pages/preparation/PlacementReadinessGatePage';
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

const mockReviews = [
  {
    id: 'rev-01',
    resume: 'res-01',
    resume_version: 1,
    student: 'stud-01',
    student_name: 'Aditi Rao',
    student_roll_number: '1GQ21CS001',
    reviewer: 'user-trainer',
    reviewer_name: 'Trainer Suresh',
    status: 'APPROVED',
    formatting_score: 9,
    technical_skills_score: 8,
    projects_score: 9,
    achievements_score: 8,
    aggregate_score: 34,
    detailed_feedback: 'Clean typography and verified technical links.',
    suggested_improvements: 'Add deployment links.',
    reviewed_at: '2026-10-26T10:00:00Z',
    created_at: '2026-10-26T10:00:00Z',
    updated_at: '2026-10-26T10:00:00Z',
  },
];

const mockTests = [
  {
    id: 'test-01',
    title: 'Quantitative & Logical Reasoning Benchmark',
    test_type: 'APTITUDE',
    domain_track: 'Quantitative Aptitude',
    description: 'Freshers aptitude evaluation.',
    duration_minutes: 30,
    total_marks: 100,
    passing_marks: 60,
    question_count: 2,
    is_active: true,
    created_by_name: 'Trainer Suresh',
    created_at: '2026-10-26T10:00:00Z',
  },
];

const mockAttempts = [
  {
    id: 'att-01',
    student: 'stud-01',
    student_name: 'Aditi Rao',
    student_roll_number: '1GQ21CS001',
    test: 'test-01',
    test_title: 'Quantitative & Logical Reasoning Benchmark',
    test_type: 'APTITUDE',
    attempt_number: 1,
    score: 80,
    total_marks: 100,
    passing_marks: 60,
    percentage: '80.00',
    passed: true,
    status: 'COMPLETED',
    answers: { '1': 'B' },
    started_at: '2026-10-26T11:00:00Z',
    completed_at: '2026-10-26T11:25:00Z',
    created_at: '2026-10-26T11:00:00Z',
  },
];

const mockMocks = [
  {
    id: 'mock-01',
    student: 'stud-01',
    student_name: 'Aditi Rao',
    student_roll_number: '1GQ21CS001',
    evaluator: 'user-eval',
    evaluator_name: 'Evaluator Rajesh',
    scheduled_by: 'user-officer',
    scheduled_by_name: 'Officer Priya',
    interview_type: 'COMBINED',
    scheduled_at: '2026-10-28T14:00:00Z',
    meeting_link: 'https://meet.google.com/test-mock',
    status: 'COMPLETED',
    notes: 'Technical & HR mock round.',
    evaluation: {
      id: 'eval-01',
      mock_interview: 'mock-01',
      evaluator: 'user-eval',
      evaluator_name: 'Evaluator Rajesh',
      technical_competence_score: 8,
      problem_solving_score: 9,
      communication_clarity_score: 8,
      professional_readiness_score: 9,
      total_score: 34,
      technical_feedback: 'Strong coding fundamentals.',
      communication_feedback: 'Confident articulation.',
      improvement_suggestions: 'Study distributed caching.',
      readiness_recommendation: 'READY_FOR_PLACEMENTS',
      evaluated_at: '2026-10-28T15:00:00Z',
    },
    created_at: '2026-10-26T10:00:00Z',
  },
];

const mockProfiles = [
  {
    id: 'stud-01',
    user: 'user-01',
    full_name: 'Aditi Rao',
    email: 'aditi.rao@gqt.edu',
    roll_number: '1GQ21CS001',
    institutional_email: 'aditi.rao@gqt.edu',
    college_name: 'GQT Engineering College',
    degree: 'B.E.',
    department: 'Computer Science',
    graduation_year: 2025,
    cgpa: '8.75',
    active_backlogs: 0,
    history_backlogs: 0,
    phone_number: '+91 98765 43210',
    is_verified_by_placement: true,
    current_resume: {
      id: 'res-01',
      version_number: 1,
      file_name: 'resume_v1.pdf',
      file_size_bytes: 45000,
      sha256_hash: 'abc',
      is_current: true,
      download_url: '/api/v1/students/resumes/res-01/download/',
      uploaded_at: '2026-10-26T09:00:00Z',
    },
  },
];

const mockSnapshot = {
  student_id: 'stud-01',
  student_name: 'Aditi Rao',
  roll_number: '1GQ21CS001',
  department: 'Computer Science',
  current_resume_id: 'res-01',
  current_resume_version: 1,
  criteria: {
    resume_review_approved: true,
    resume_review_id: 'rev-01',
    aptitude_assessment_passed: true,
    aptitude_score: 80,
    technical_assessment_passed: true,
    technical_score: 85,
    communication_attended: true,
    grooming_certified: true,
    mock_interview_completed: true,
    mock_interview_ready: true,
    mock_total_score: 34,
  },
  all_criteria_met: true,
  is_placement_certified: true,
  current_certification: {
    is_approved_for_placements: true,
    status: 'CERTIFIED',
    certified_by: 'Placement Head Sharma',
    certified_at: '2026-10-26T12:00:00Z',
    notes: 'Certified ready for placement drives.',
  },
};

describe('Frontend Student Preparation Suite (Phase 6 / Steps 15-23)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Default current user mock
    vi.mocked(apiClient.get).mockImplementation(async (url: string) => {
      if (url.includes('/auth/me/')) {
        return {
          data: {
            id: 'user-admin',
            email: 'head@gqt.internal',
            first_name: 'Placement',
            last_name: 'Head',
            full_name: 'Placement Head Sharma',
            roles: ['PLACEMENT_HEAD', 'ADMIN', 'TRAINER', 'EVALUATOR'],
            is_staff: true,
            is_superuser: true,
          },
        };
      }
      if (url === '/preparation/resume-reviews/') {
        return { data: mockReviews };
      }
      if (url === '/preparation/improvement-cycles/') {
        return { data: [] };
      }
      if (url === '/preparation/tests/') {
        return { data: mockTests };
      }
      if (url === '/preparation/attempts/') {
        return { data: mockAttempts };
      }
      if (url === '/preparation/mock-interviews/') {
        return { data: mockMocks };
      }
      if (url === '/students/profiles/') {
        return { data: mockProfiles };
      }
      if (url === '/preparation/certifications/') {
        return { data: [] };
      }
      if (url.startsWith('/preparation/readiness-snapshot/')) {
        return { data: mockSnapshot };
      }
      return { data: [] };
    });
  });

  it('renders ResumeReviewWorkspacePage with KPI metrics and reviews list (Step 15)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/resume-reviews']}>
            <ResumeReviewWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    expect(screen.getByText(/Loading resume reviews/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Resume Review & Improvement Cycle')).toBeInTheDocument();
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
      expect(screen.getByText('1GQ21CS001')).toBeInTheDocument();
      expect(screen.getByText('Approved')).toBeInTheDocument();
      expect(screen.getByText('34 / 40')).toBeInTheDocument();
    });
  });

  it('renders trainer rubric review modal on button click (Step 15)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/resume-reviews']}>
            <ResumeReviewWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Resume Review & Improvement Cycle')).toBeInTheDocument();
    });

    const reviewBtn = screen.getByRole('button', { name: /Conduct Rubric Review/i });
    fireEvent.click(reviewBtn);

    expect(screen.getByText(/Conduct Resume Rubric Review \(Step 15\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Detailed Evaluation Comments/i)).toBeInTheDocument();
  });

  it('renders StudentAssessmentsPage with test modules and attempt history (Steps 17 & 18)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/assessments']}>
            <StudentAssessmentsPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Student Assessments Engine')).toBeInTheDocument();
      expect(screen.getAllByText('Quantitative & Logical Reasoning Benchmark')[0]).toBeInTheDocument();
      expect(screen.getByText('80 / 100')).toBeInTheDocument();
      expect(screen.getByText('80.00%')).toBeInTheDocument();
      expect(screen.getByText('PASSED')).toBeInTheDocument();
    });
  });

  it('renders MockInterviewWorkspacePage with completed sessions and rubric scorecards (Steps 21 & 22)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/mock-interviews']}>
            <MockInterviewWorkspacePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('One-on-One Mock Interviews & Rubrics')).toBeInTheDocument();
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('Schedule Mock Interview')).toBeInTheDocument();
    });
  });

  it('renders PlacementReadinessGatePage with candidate readiness roster and criteria (Step 23 Gate)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/readiness-gate']}>
            <PlacementReadinessGatePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Final Placement Resume Approval Gate')).toBeInTheDocument();
      expect(screen.getByText('Candidate Readiness Roster')).toBeInTheDocument();
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
    });

    // Click candidate to inspect criteria
    const viewBtn = screen.getByRole('button', { name: /View Criteria/i });
    fireEvent.click(viewBtn);

    await waitFor(() => {
      expect(screen.getByText('1. Resume Review (Step 15)')).toBeInTheDocument();
      expect(screen.getByText('2. Aptitude Test (Step 17)')).toBeInTheDocument();
      expect(screen.getByText('3. Technical Test (Step 18)')).toBeInTheDocument();
      expect(screen.getByText('5. Corporate Grooming (Step 20)')).toBeInTheDocument();
      expect(screen.getByText('6. Mock Interview (Step 22)')).toBeInTheDocument();
    });
  });

  it('allows Placement Head to open certification decision modal (Step 23 Gate)', async () => {
    render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/preparation/readiness-gate']}>
            <PlacementReadinessGatePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
    });

    const viewBtn = screen.getByRole('button', { name: /View Criteria/i });
    fireEvent.click(viewBtn);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Placement Head Certification Decision/i })).toBeInTheDocument();
    });

    const certBtn = screen.getByRole('button', { name: /Placement Head Certification Decision/i });
    fireEvent.click(certBtn);

    expect(screen.getByText(/Placement Readiness Certification Gate \(Step 23\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Authorize Clearance/i)).toBeInTheDocument();
  });
});
