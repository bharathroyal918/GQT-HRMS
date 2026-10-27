import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { FeedbackWorkspacePage } from '../pages/feedback/FeedbackWorkspacePage';
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

const mockKPIs = {
  total_student_feedback: 14,
  total_hr_feedback: 9,
  total_trainer_feedback: 18,
  avg_technical_skills_rating: 4.2,
  avg_communication_skills_rating: 4.1,
  avg_hiring_satisfaction_rating: 4.5,
  avg_training_effectiveness_rating: 4.4,
  difficulty_breakdown: { EASY: 2, MEDIUM: 8, HARD: 3, VERY_HARD: 1 },
  readiness_breakdown: { HIGHLY_READY: 6, READY: 8, NEEDS_PRACTICE: 3, NOT_READY: 1 },
};

const mockStudentFeedbacks = [
  {
    id: 'sfb-001',
    student: 'stud-001',
    student_name: 'Aarav Sharma',
    student_roll_number: '1GQ22CS001',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    job_requirement: 'job-001',
    job_title: 'Junior Software Engineer',
    interview_schedule: 'sched-001',
    interview_date: '2026-10-27',
    interview_round: 'Technical Round 1',
    interview_experience: 'Two interviewers who were very friendly and focused on data structures and algorithms.',
    technical_questions: 'Reverse a singly linked list in-place; explain B-trees and database indexing.',
    difficulty: 'MEDIUM',
    difficulty_display: 'Medium',
    suggestions: 'Practice standard LeetCode problems and write clean comments.',
    is_anonymous: false,
    submitted_by: 'user-001',
    submitted_by_name: 'Aarav Sharma',
    created_at: '2026-10-27T08:30:00Z',
    updated_at: '2026-10-27T08:30:00Z',
  },
  {
    id: 'sfb-002',
    student: 'stud-002',
    student_name: 'Anonymous Candidate',
    student_roll_number: 'ANONYMOUS',
    company: 'comp-002',
    company_name: 'InnovateX Solutions',
    job_requirement: 'job-002',
    job_title: 'Cloud Analyst',
    interview_schedule: null,
    interview_date: null,
    interview_round: null,
    interview_experience: 'Rigorous round on distributed systems and networking fundamentals with live terminal tests.',
    technical_questions: 'Explain TCP handshake and handle split-brain scenarios in Raft consensus.',
    difficulty: 'HARD',
    difficulty_display: 'Hard',
    suggestions: 'Deep dive into computer networking protocols.',
    is_anonymous: true,
    submitted_by: 'user-002',
    submitted_by_name: 'Anonymous Candidate',
    created_at: '2026-10-27T09:00:00Z',
    updated_at: '2026-10-27T09:00:00Z',
  },
];

const mockHRFeedbacks = [
  {
    id: 'hrfb-001',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sarah Jenkins',
    job_requirement: 'job-001',
    job_title: 'Junior Software Engineer',
    candidate: 'cand-001',
    candidate_name: 'Aarav Sharma',
    candidate_roll_number: '1GQ22CS001',
    candidate_quality: 'EXCELLENT',
    candidate_quality_display: 'Excellent',
    candidate_quality_remarks: 'Candidate displayed deep computer science fundamentals and structured thought process.',
    technical_skills_rating: 5,
    technical_skills_remarks: 'Flawless execution on algorithm questions.',
    communication_skills_rating: 4,
    communication_skills_remarks: 'Articulate, calm under pressure.',
    hiring_satisfaction_rating: 5,
    hiring_satisfaction_remarks: 'Highly pleased with student readiness from GQT.',
    submitted_by: 'user-hr-001',
    submitted_by_name: 'Sarah Jenkins',
    created_at: '2026-10-27T09:30:00Z',
    updated_at: '2026-10-27T09:30:00Z',
  },
];

const mockTrainerFeedbacks = [
  {
    id: 'trfb-001',
    student: 'stud-001',
    student_name: 'Aarav Sharma',
    student_roll_number: '1GQ22CS001',
    training_session: 'sess-001',
    session_title: 'Full Stack Java Bootcamp Batch 2026',
    student_readiness: 'HIGHLY_READY',
    student_readiness_display: 'Highly Ready',
    student_readiness_remarks: 'Consistently completes advanced lab assignments and mentors peers.',
    training_effectiveness_rating: 5,
    training_effectiveness_remarks: 'Cohort fully absorbed modern Spring Boot patterns.',
    areas_for_improvement: 'Continue polishing system design diagrams for large-scale microservice architectures.',
    trainer: 'user-tr-001',
    trainer_name: 'Prof. Ramesh Kulkarni',
    created_at: '2026-10-27T10:00:00Z',
    updated_at: '2026-10-27T10:00:00Z',
  },
];

const mockEligibleDrives = [
  {
    interview_schedule_id: 'sched-001',
    company_id: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    job_requirement_id: 'job-001',
    job_title: 'Junior Software Engineer',
    interview_date: '2026-10-27',
  },
];

describe('Feedback Collection Workspace (Phase 9)', () => {
  let queryClient: QueryClient;

  const setupDefaultMocks = (role: string = 'ADMIN') => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'test-user-id',
            email: 'test@gqt.internal',
            full_name: 'Test Administrator',
            roles: [role],
            role_assignments: [{ id: 'ra-1', role: { code: role, name: role }, is_active: true }],
            is_active: true,
            is_staff: role === 'ADMIN' || role === 'PLACEMENT_OFFICER',
            is_superuser: role === 'ADMIN',
          },
        });
      }
      if (url.includes('/feedback/summary/')) {
        return Promise.resolve({ data: mockKPIs });
      }
      if (url.includes('/feedback/student-eligible-drives/')) {
        return Promise.resolve({ data: { data: mockEligibleDrives, success: true } });
      }
      if (url.includes('/feedback/student/')) {
        return Promise.resolve({ data: { data: mockStudentFeedbacks, success: true } });
      }
      if (url.includes('/feedback/hr/')) {
        return Promise.resolve({ data: { data: mockHRFeedbacks, success: true } });
      }
      if (url.includes('/feedback/trainer/')) {
        return Promise.resolve({ data: { data: mockTrainerFeedbacks, success: true } });
      }
      return Promise.resolve({ data: [] });
    });

    (apiClient.post as any).mockImplementation((url: string, payload: any) => {
      if (url.includes('/feedback/student/')) {
        return Promise.resolve({
          data: {
            ...mockStudentFeedbacks[0],
            id: 'sfb-new-001',
            company_name: payload.company,
            interview_experience: payload.interview_experience,
            difficulty: payload.difficulty,
          },
        });
      }
      if (url.includes('/feedback/hr/')) {
        return Promise.resolve({
          data: {
            ...mockHRFeedbacks[0],
            id: 'hrfb-new-001',
            company_name: payload.company,
            technical_skills_rating: payload.technical_skills_rating,
          },
        });
      }
      if (url.includes('/feedback/trainer/')) {
        return Promise.resolve({
          data: {
            ...mockTrainerFeedbacks[0],
            id: 'trfb-new-001',
            areas_for_improvement: payload.areas_for_improvement,
          },
        });
      }
      return Promise.resolve({ data: {} });
    });
  };

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>{ui}</MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

  beforeEach(() => {
    setupDefaultMocks('ADMIN');
  });

  it('renders Feedback Workspace with KPI summary banner and Student Interview Experiences list', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    expect(await screen.findByText('Feedback Collection Workspace')).toBeInTheDocument();
    expect(screen.getByText('Phase 9')).toBeInTheDocument();

    // Verify KPI summary cards
    expect(await screen.findByText('Student Feedback')).toBeInTheDocument();
    expect(screen.getByText('HR Evaluations')).toBeInTheDocument();
    expect(screen.getByText('Trainer Feedback')).toBeInTheDocument();
    expect(screen.getByText('Avg Tech Rating')).toBeInTheDocument();
    expect(screen.getByText('Avg Comm Rating')).toBeInTheDocument();
    expect(screen.getByText('Avg Satisfaction')).toBeInTheDocument();

    // Verify Category A Student Feedback items
    expect(await screen.findByText('TechCorp Global Ltd')).toBeInTheDocument();
    expect(screen.getByText('InnovateX Solutions')).toBeInTheDocument();
    expect(screen.getByText('Reverse a singly linked list in-place; explain B-trees and database indexing.')).toBeInTheDocument();
    expect(screen.getAllByText('Medium').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Hard').length).toBeGreaterThan(0);
  });

  it('allows opening and submitting Share Interview Experience modal (Category A)', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Click "Add Student Feedback" (or Share Interview Experience)
    const addBtn = await screen.findByRole('button', { name: /Add Student Feedback/i });
    fireEvent.click(addBtn);

    // Verify Modal opens
    expect(await screen.findByText('Share Interview Experience')).toBeInTheDocument();
    expect(screen.getByText('Category A: Technical questions, difficulty, suggestions')).toBeInTheDocument();

    // Fill form
    const companyInput = screen.getByLabelText(/Company Name \/ ID \*/i);
    fireEvent.change(companyInput, { target: { value: 'Google India' } });

    const experienceInput = screen.getByLabelText(/Interview Experience Narrative \*/i);
    fireEvent.change(experienceInput, {
      target: { value: 'Very deep and insightful technical rounds testing concurrency and algorithmic scalability.' },
    });

    const submitBtn = screen.getByRole('button', { name: /Submit Feedback/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/feedback/student/',
        expect.objectContaining({
          company: 'Google India',
          difficulty: 'MEDIUM',
          interview_experience: 'Very deep and insightful technical rounds testing concurrency and algorithmic scalability.',
        })
      );
    });

    expect(await screen.findByText('Interview experience feedback submitted successfully!')).toBeInTheDocument();
  });

  it('switches to Corporate HR Feedback tab and displays recruiter evaluations and ratings (Category B)', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Click "Corporate HR Feedback" tab
    const hrTab = await screen.findByRole('button', { name: /Corporate HR Feedback/i });
    fireEvent.click(hrTab);

    // Verify HR items are displayed
    expect(await screen.findByText('TechCorp Global Ltd')).toBeInTheDocument();
    expect(screen.getByText(/Sarah Jenkins/)).toBeInTheDocument();
    expect(screen.getByText('Candidate displayed deep computer science fundamentals and structured thought process.')).toBeInTheDocument();
    expect(screen.getAllByText('Excellent').length).toBeGreaterThan(0);
    expect(screen.getByText('Flawless execution on algorithm questions.')).toBeInTheDocument();
  });

  it('allows opening and submitting Record HR Feedback modal (Category B)', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Switch to HR tab
    const hrTab = await screen.findByRole('button', { name: /Corporate HR Feedback/i });
    fireEvent.click(hrTab);

    // Click "Record HR Feedback" header button
    const recordBtns = await screen.findAllByRole('button', { name: /Record HR Feedback/i });
    fireEvent.click(recordBtns[0]!);

    // Verify HR modal is open
    expect(await screen.findByText('Record Corporate HR Feedback')).toBeInTheDocument();

    // Fill company
    const companyInput = screen.getByLabelText(/Company ID \/ Name \*/i);
    fireEvent.change(companyInput, { target: { value: 'Oracle Financial Services' } });

    // Submit via form submit button
    const submitBtns = screen.getAllByRole('button', { name: /Record HR Feedback/i });
    fireEvent.click(submitBtns[submitBtns.length - 1]!);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/feedback/hr/',
        expect.objectContaining({
          company: 'Oracle Financial Services',
          candidate_quality: 'GOOD',
          technical_skills_rating: 4,
          communication_skills_rating: 4,
          hiring_satisfaction_rating: 4,
        })
      );
    });

    expect(await screen.findByText('Corporate HR evaluation recorded successfully!')).toBeInTheDocument();
  });

  it('switches to Trainer Readiness Feedback tab and displays evaluation cards (Category C)', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Click Trainer tab
    const trainerTab = await screen.findByRole('button', { name: /Trainer Readiness Feedback/i });
    fireEvent.click(trainerTab);

    // Verify Trainer items
    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();
    expect(screen.getByText(/Prof. Ramesh Kulkarni/)).toBeInTheDocument();
    expect(screen.getAllByText('Highly Ready').length).toBeGreaterThan(0);
    expect(screen.getByText('Full Stack Java Bootcamp Batch 2026')).toBeInTheDocument();
    expect(screen.getByText('Continue polishing system design diagrams for large-scale microservice architectures.')).toBeInTheDocument();
  });

  it('allows opening and submitting Record Trainer Feedback modal (Category C)', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Switch to Trainer tab
    const trainerTab = await screen.findByRole('button', { name: /Trainer Readiness Feedback/i });
    fireEvent.click(trainerTab);

    // Click "Record Trainer Feedback" button
    const recordBtns = await screen.findAllByRole('button', { name: /Record Trainer Feedback/i });
    fireEvent.click(recordBtns[0]!);

    // Verify Trainer modal is open
    expect(await screen.findByText('Record Trainer Readiness Feedback')).toBeInTheDocument();

    // Fill form
    const studentInput = screen.getByLabelText(/Student Profile ID \/ Roll Number \*/i);
    fireEvent.change(studentInput, { target: { value: '1GQ22CS099' } });

    const areasInput = screen.getByLabelText(/Areas for Improvement \*/i);
    fireEvent.change(areasInput, {
      target: { value: 'Needs more practice with recursive backtracking and dynamic programming memoization.' },
    });

    const submitBtns = screen.getAllByRole('button', { name: /Record Trainer Feedback/i });
    fireEvent.click(submitBtns[submitBtns.length - 1]!);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/feedback/trainer/',
        expect.objectContaining({
          student: '1GQ22CS099',
          student_readiness: 'READY',
          training_effectiveness_rating: 4,
          areas_for_improvement: 'Needs more practice with recursive backtracking and dynamic programming memoization.',
        })
      );
    });

    expect(await screen.findByText('Trainer evaluation submitted successfully!')).toBeInTheDocument();
  });

  it('enforces Student role isolation: hides Corporate HR and Trainer tabs', async () => {
    setupDefaultMocks('STUDENT');
    renderWithProviders(<FeedbackWorkspacePage />);

    // Renders My Interview Experiences tab
    expect(await screen.findByText('My Interview Experiences')).toBeInTheDocument();

    // Corporate HR Feedback and Trainer Feedback tabs must NOT exist
    expect(screen.queryByText('Corporate HR Feedback')).not.toBeInTheDocument();
    expect(screen.queryByText('Trainer Readiness Feedback')).not.toBeInTheDocument();

    // Renders "Share Interview Experience" action button
    expect(screen.getByRole('button', { name: /Share Interview Experience/i })).toBeInTheDocument();
  });

  it('enforces Trainer role isolation: defaults to Trainer tab and hides Corporate HR feedback', async () => {
    setupDefaultMocks('TRAINER');
    renderWithProviders(<FeedbackWorkspacePage />);

    // Renders Trainer Readiness Feedback tab
    expect(await screen.findByText('Trainer Readiness Feedback')).toBeInTheDocument();

    // Corporate HR Feedback tab must NOT exist for trainer
    expect(screen.queryByText('Corporate HR Feedback')).not.toBeInTheDocument();

    // Student tab is also hidden for trainer-only
    expect(screen.queryByText('Student Interview Experiences')).not.toBeInTheDocument();
  });

  it('opens detail modal to safely view full feedback record', async () => {
    renderWithProviders(<FeedbackWorkspacePage />);

    // Click "View Full" button on student card
    const viewButtons = await screen.findAllByRole('button', { name: /View Full/i });
    fireEvent.click(viewButtons[0]!);

    // Verify modal appears
    expect(await screen.findByText('TechCorp Global Ltd — Interview Experience')).toBeInTheDocument();
    expect(screen.getAllByText('Reverse a singly linked list in-place; explain B-trees and database indexing.').length).toBeGreaterThan(0);

    // Click "Close"
    const closeBtn = screen.getByRole('button', { name: /Close/i });
    fireEvent.click(closeBtn);

    await waitFor(() => {
      expect(screen.queryByText('TechCorp Global Ltd — Interview Experience')).not.toBeInTheDocument();
    });
  });
});
