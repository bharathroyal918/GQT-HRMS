import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { InterviewWorkspacePage } from '../pages/interviews/InterviewWorkspacePage';
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
  total_shortlists: 2,
  total_shortlisted_candidates: 10,
  total_schedules: 5,
  confirmed_attendance: 4,
  interviews_conducted: 2,
  pending_hr_followups: 1,
};

const mockJobs = [
  {
    id: 'job-001',
    title: 'Senior Software Engineer',
    company: 'comp-001',
    company_name: 'Google LLC',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sundar Recruiter',
    status: 'APPROVED',
  },
];

const mockSchedules = [
  {
    id: 'sched-001',
    job_requirement: 'job-001',
    company: 'comp-001',
    company_name: 'Google LLC',
    job_title: 'Senior Software Engineer',
    candidate: 'stud-001',
    student: 'stud-001',
    candidate_name: 'Aditi Rao',
    candidate_roll: '1GQ21CS101',
    candidate_email: 'aditi.rao@gqt.edu',
    candidate_phone: '+919876543210',
    schedule_reference_code: 'SCH-20261027-0001',
    mode: 'ONLINE',
    mode_display: 'Online Interview',
    interview_date: '2026-10-30',
    interview_time: '10:00:00',
    scheduled_start_time: '2026-10-30T10:00:00+05:30',
    venue: '',
    meeting_link: 'https://meet.google.com/abc-defg-hij',
    required_documents: 'Resume, ID card',
    status: 'SCHEDULED',
    status_display: 'Scheduled',
    rescheduled_from: null,
    is_superseded: false,
    notified_at: '2026-10-27T09:05:00Z',
    attendance_status: 'NO_RESPONSE',
    attendance_status_display: 'No Response Yet',
    attendance_confirmed_at: null,
    attendance_confirmed_by: null,
    attendance_confirmed_by_name: '',
    attendance_source: 'PENDING_INPUT',
    attendance_notes: '',
    conducted_status: 'NOT_CONDUCTED',
    conducted_status_display: 'Not Conducted',
    conducted_at: null,
    conducted_recorded_by: null,
    conducted_recorded_by_name: '',
    conducted_notes: '',
    created_by: 'user-head',
    created_by_name: 'Placement Officer',
    notification_status: 'SENT',
    created_at: '2026-10-27T09:00:00Z',
    reminders: [
      {
        id: 'rem-1',
        interval: '24_HOURS',
        interval_display: '24 Hours Prior',
        scheduled_for: '2026-10-29T10:00:00Z',
        status: 'SCHEDULED',
        status_display: 'Scheduled',
        sent_at: null,
        channel: 'EMAIL',
        provider_message_id: '',
        error_message: '',
        attempt_count: 0,
      },
      {
        id: 'rem-2',
        interval: '2_HOURS',
        interval_display: '2 Hours Prior',
        scheduled_for: '2026-10-30T08:00:00Z',
        status: 'SCHEDULED',
        status_display: 'Scheduled',
        sent_at: null,
        channel: 'EMAIL',
        provider_message_id: '',
        error_message: '',
        attempt_count: 0,
      },
      {
        id: 'rem-3',
        interval: '30_MINUTES',
        interval_display: '30 Minutes Prior',
        scheduled_for: '2026-10-30T09:30:00Z',
        status: 'SCHEDULED',
        status_display: 'Scheduled',
        sent_at: null,
        channel: 'EMAIL',
        provider_message_id: '',
        error_message: '',
        attempt_count: 0,
      },
    ],
    notification_logs: [],
  },
];

const mockShortlists = [
  {
    id: 'sl-001',
    shortlist_reference_code: 'SL-20261027-0001',
    job_requirement: 'job-001',
    job_title: 'Senior Software Engineer',
    company: 'comp-001',
    company_name: 'Google LLC',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sundar Recruiter',
    submission_package: null,
    source: 'EMAIL_ATTACHMENT',
    candidate_count: 1,
    candidates: [
      {
        id: 'sc-001',
        student_id: 'stud-001',
        roll_number: '1GQ21CS101',
        full_name: 'Aditi Rao',
        email: 'aditi.rao@gqt.edu',
        phone_number: '+919876543210',
        department: 'Computer Science',
        degree: 'B.Tech',
        cgpa: 8.85,
        status: 'SHORTLISTED',
        recruiter_notes: '',
        active_schedule_id: null,
        created_at: '2026-10-27T08:00:00Z',
      },
    ],
    received_at: '2026-10-27T08:00:00Z',
    created_at: '2026-10-27T08:00:00Z',
    created_by: 'user-head',
    created_by_name: 'Placement Officer',
    notes: 'HR approved roster.',
  },
];

const mockRounds = [
  {
    id: 'rnd-001',
    job_requirement: 'job-001',
    job_title: 'Senior Software Engineer',
    candidate: 'stud-001',
    candidate_name: 'Aditi Rao',
    candidate_roll: '1GQ21CS101',
    category: 'TECHNICAL',
    category_display: 'Technical Interview',
    round_number: 1,
    round_name: 'Technical Round 1',
    interviewer_names: 'Alex Lead Architect',
    scheduled_date: '2026-10-30',
    scheduled_time: '10:00:00',
    status: 'SCHEDULED',
    status_display: 'Scheduled',
    evaluated_by: null,
    evaluated_by_name: null,
    evaluated_at: null,
    internal_staff_notes: 'Focus on distributed systems design.',
    created_at: '2026-10-27T09:30:00Z',
  },
];

const mockFollowUps = [
  {
    id: 'fu-001',
    job_requirement: 'job-001',
    company: 'comp-001',
    company_name: 'Google LLC',
    job_title: 'Senior Software Engineer',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sundar Recruiter',
    follow_up_date: '2026-10-27',
    channel: 'PHONE',
    channel_display: 'Phone Call',
    conducted_by: 'user-head',
    conducted_by_name: 'Placement Officer',
    candidate_status_reported: 'Shortlisted candidates under Round 1 technical review.',
    pending_rounds: 'Managerial round pending for top 3 scorers.',
    expected_result_date: '2026-11-05',
    is_date_confirmed: true,
    next_follow_up_date: '2026-11-02',
    response_status: 'RESPONSE_RECEIVED',
    response_status_display: 'Response Received',
    hr_response_summary: 'Spoke with Sundar via phone. All good.',
    notes: '',
    created_at: '2026-10-27T09:45:00Z',
  },
];

const mockSubmittableCandidates = [
  {
    submission_id: 'sub-001',
    student_id: 'stud-001',
    student_name: 'Aditi Rao',
    roll_number: '1GQ21CS101',
    institutional_email: 'aditi.rao@gqt.edu',
    status: 'SUBMITTED',
  },
];

describe('Frontend Interview Management & Tracking Suite (Phase 8 / Steps 29-35)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Default mock implementation
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-head',
            email: 'head@gqt.internal',
            full_name: 'Placement Head Officer',
            first_name: 'Placement',
            last_name: 'Head',
            roles: ['PLACEMENT_HEAD', 'ADMIN'],
            role_assignments: [
              { id: 'ra-1', role: { code: 'PLACEMENT_HEAD', name: 'Placement Head' }, is_active: true },
            ],
            is_active: true,
            is_staff: true,
            is_superuser: true,
          },
        });
      }
      if (url.includes('/interviews/kpis/')) {
        return Promise.resolve({ data: mockKPIs });
      }
      if (url.includes('/interviews/schedules/my/')) {
        return Promise.resolve({ data: mockSchedules });
      }
      if (url.includes('/interviews/schedules/')) {
        return Promise.resolve({ data: mockSchedules });
      }
      if (url.includes('/interviews/shortlists/submittables/')) {
        return Promise.resolve({ data: mockSubmittableCandidates });
      }
      if (url.includes('/interviews/shortlists/')) {
        return Promise.resolve({ data: mockShortlists });
      }
      if (url.includes('/interviews/rounds/')) {
        return Promise.resolve({ data: mockRounds });
      }
      if (url.includes('/interviews/follow-ups/')) {
        return Promise.resolve({ data: mockFollowUps });
      }
      if (url.includes('/jobs/')) {
        return Promise.resolve({ data: { data: mockJobs, results: mockJobs } });
      }
      return Promise.resolve({ data: [] });
    });

    (apiClient.post as any).mockImplementation((url: string) => {
      if (url.includes('/interviews/reminders/process-due/')) {
        return Promise.resolve({
          data: { message: 'Processed 3 due reminder notifications successfully.' },
        });
      }
      if (url.includes('/notify/')) {
        return Promise.resolve({
          data: { message: 'Student notification queued.' },
        });
      }
      if (url.includes('/confirm-attendance/')) {
        return Promise.resolve({
          data: { message: 'Attendance confirmed.' },
        });
      }
      if (url.includes('/record-conducted/')) {
        return Promise.resolve({
          data: { message: 'Interview conducted outcome saved.' },
        });
      }
      if (url.includes('/evaluate/')) {
        return Promise.resolve({
          data: { message: 'Round evaluation recorded.' },
        });
      }
      if (url.includes('/interviews/shortlists/')) {
        return Promise.resolve({ data: mockShortlists[0] });
      }
      if (url.includes('/interviews/schedules/')) {
        return Promise.resolve({ data: mockSchedules[0] });
      }
      if (url.includes('/interviews/rounds/')) {
        return Promise.resolve({ data: mockRounds[0] });
      }
      if (url.includes('/interviews/follow-ups/')) {
        return Promise.resolve({ data: mockFollowUps[0] });
      }
      return Promise.resolve({ data: {} });
    });
  });

  const renderWorkspace = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>
          <AuthProvider>
            <InterviewWorkspacePage />
          </AuthProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders workspace with KPI metrics and tab navigation', async () => {
    renderWorkspace();

    // Verify Title and Subtitle
    await waitFor(() => {
      expect(screen.getByText('Interview Management & Tracking')).toBeInTheDocument();
    });
    expect(screen.getByText(/Workflow Steps 29–35/i)).toBeInTheDocument();

    // Verify KPI Cards values
    await waitFor(() => {
      expect(screen.getByText('Shortlists')).toBeInTheDocument();
      expect(screen.getByText('Active Sessions')).toBeInTheDocument();
      expect(screen.getByText('Confirmed Ready')).toBeInTheDocument();
      expect(screen.getByText('Completed Sessions')).toBeInTheDocument();
      expect(screen.getByText('Rounds Logged')).toBeInTheDocument();
      expect(screen.getByText('Scheduled Callbacks')).toBeInTheDocument();
    });

    // Verify Tab buttons
    expect(screen.getByTestId('tab-schedules')).toBeInTheDocument();
    expect(screen.getByTestId('tab-shortlists')).toBeInTheDocument();
    expect(screen.getByTestId('tab-rounds')).toBeInTheDocument();
    expect(screen.getByTestId('tab-followups')).toBeInTheDocument();
  });

  it('Step 29: displays shortlisted candidates and allows opening intake modal', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('tab-shortlists')).toBeInTheDocument();
    });

    // Click HR Shortlists Tab
    fireEvent.click(screen.getByTestId('tab-shortlists'));

    // Verify Shortlist reference code is visible
    await waitFor(() => {
      expect(screen.getByText('SL-20261027-0001')).toBeInTheDocument();
      expect(screen.getByText('Sundar Recruiter')).toBeInTheDocument();
    });

    // Click "Intake HR Shortlist" button
    const intakeBtn = screen.getByTestId('intake-shortlist-button');
    expect(intakeBtn).toBeInTheDocument();
    fireEvent.click(intakeBtn);

    // Modal should be open
    await waitFor(() => {
      expect(screen.getByText('Receive Candidate Shortlist (Step 29)')).toBeInTheDocument();
      expect(screen.getByTestId('shortlist-job-select')).toBeInTheDocument();
    });
  });

  it('Step 30 & 31: displays interview schedule, reminders modal trigger, and allows notifying student', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
      expect(screen.getByText('1GQ21CS101')).toBeInTheDocument();
      expect(screen.getByText('Google LLC')).toBeInTheDocument();
      expect(screen.getByText('2026-10-30')).toBeInTheDocument();
      expect(screen.getByText('10:00:00')).toBeInTheDocument();
    });

    // Verify Reminders trigger button is present
    const remindersBtn = screen.getByTestId('reminders-btn-sched-001');
    expect(remindersBtn).toBeInTheDocument();
    fireEvent.click(remindersBtn);

    await waitFor(() => {
      expect(screen.getByText('Automatic Reminders (Step 31)')).toBeInTheDocument();
      expect(screen.getByText(/24 Hours Prior/i)).toBeInTheDocument();
      expect(screen.getByText(/2 Hours Prior/i)).toBeInTheDocument();
      expect(screen.getByText(/30 Minutes Prior/i)).toBeInTheDocument();
    });

    // Close modal
    fireEvent.click(screen.getByText('✕'));

    // Verify Notify Student button
    const notifyBtn = screen.getByTestId('notify-btn-sched-001');
    expect(notifyBtn).toBeInTheDocument();
    fireEvent.click(notifyBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/interviews/schedules/sched-001/notify/',
        { channel: 'EMAIL' }
      );
    });
  });

  it('Step 31: allows triggering automatic reminder scheduler', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('process-reminders-button')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('process-reminders-button'));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/interviews/reminders/process-due/'
      );
    });
  });

  it('Step 32: allows recording attendance confirmation', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('confirm-attendance-btn-sched-001')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('confirm-attendance-btn-sched-001'));

    await waitFor(() => {
      expect(screen.getByText('Confirm Attendance (Step 32)')).toBeInTheDocument();
      expect(screen.getByTestId('attendance-choice-select')).toBeInTheDocument();
    });

    // Select DECLINED and submit
    fireEvent.change(screen.getByTestId('attendance-choice-select'), { target: { value: 'DECLINED' } });
    fireEvent.change(screen.getByPlaceholderText(/Optional notes or reason if declining.../i), {
      target: { value: 'Student has a medical conflict.' },
    });

    const submitBtn = screen.getByTestId('save-attendance-btn');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/interviews/schedules/sched-001/confirm-attendance/',
        expect.objectContaining({
          attendance_status: 'DECLINED',
          notes: 'Student has a medical conflict.',
        })
      );
    });
  });

  it('Step 33: allows recording interview conducted outcome', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('conducted-btn-sched-001')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('conducted-btn-sched-001'));

    await waitFor(() => {
      expect(screen.getByText('Record Interview Conducted (Step 33)')).toBeInTheDocument();
      expect(screen.getByTestId('conducted-choice-select')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('conducted-choice-select'), { target: { value: 'CONDUCTED' } });
    fireEvent.change(screen.getByPlaceholderText(/Observations from the interview drive.../i), {
      target: { value: 'Successfully conducted by Alex.' },
    });

    const submitBtn = screen.getByTestId('save-conducted-btn');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/interviews/schedules/sched-001/record-conducted/',
        expect.objectContaining({
          conducted_status: 'CONDUCTED',
          notes: 'Successfully conducted by Alex.',
        })
      );
    });
  });

  it('Step 34: displays interview rounds and allows evaluating round outcome', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('tab-rounds')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('tab-rounds'));

    await waitFor(() => {
      expect(screen.getByText('Technical Round 1')).toBeInTheDocument();
      expect(screen.getByText('Alex Lead Architect')).toBeInTheDocument();
      expect(screen.getByText('Technical Interview')).toBeInTheDocument();
    });

    // Click Evaluate
    const evalBtn = screen.getByTestId('eval-round-btn-rnd-001');
    fireEvent.click(evalBtn);

    await waitFor(() => {
      expect(screen.getByText('Evaluate Round (Step 34)')).toBeInTheDocument();
      expect(screen.getByTestId('eval-round-status-select')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByTestId('eval-round-status-select'), { target: { value: 'CLEARED' } });
    fireEvent.change(screen.getByPlaceholderText(/Interviewer scorecard notes.../i), {
      target: { value: 'Excellent problem solving.' },
    });

    const submitBtn = screen.getByTestId('save-round-eval-btn');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith(
        '/interviews/rounds/rnd-001/evaluate/',
        expect.objectContaining({
          status: 'CLEARED',
          internal_staff_notes: 'Excellent problem solving.',
        })
      );
    });
  });

  it('Step 35: displays HR follow-ups and allows recording corporate follow-up', async () => {
    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByTestId('tab-followups')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId('tab-followups'));

    await waitFor(() => {
      expect(screen.getByText(/Shortlisted candidates under Round 1/i)).toBeInTheDocument();
      expect(screen.getByText(/Managerial round pending for top 3 scorers/i)).toBeInTheDocument();
      expect(screen.getByText(/2026-11-05/)).toBeInTheDocument();
    });

    const logBtn = screen.getByTestId('log-followup-button');
    fireEvent.click(logBtn);

    await waitFor(() => {
      expect(screen.getByText('Log HR Follow-up (Step 35)')).toBeInTheDocument();
      expect(screen.getByTestId('followup-candidate-status-input')).toBeInTheDocument();
    });
  });

  it('Student role isolation: students cannot view staff-only tabs or action buttons', async () => {
    // Mock user as a Student
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-student',
            email: 'student@gqt.edu',
            full_name: 'Aditi Rao',
            first_name: 'Aditi',
            last_name: 'Rao',
            roles: ['STUDENT'],
            role_assignments: [
              { id: 'ra-student', role: { code: 'STUDENT', name: 'Student' }, is_active: true },
            ],
            is_active: true,
            is_staff: false,
            is_superuser: false,
          },
        });
      }
      if (url.includes('/interviews/my-interviews/')) {
        return Promise.resolve({ data: mockSchedules });
      }
      return Promise.resolve({ data: [] });
    });

    renderWorkspace();

    await waitFor(() => {
      expect(screen.getByText('Interview Management & Tracking')).toBeInTheDocument();
    });

    // Staff buttons should NOT be in the document
    expect(screen.queryByTestId('process-reminders-button')).not.toBeInTheDocument();
    expect(screen.queryByTestId('intake-shortlist-button')).not.toBeInTheDocument();

    // Staff-only tabs should NOT be in the document
    expect(screen.queryByTestId('tab-shortlists')).not.toBeInTheDocument();
    expect(screen.queryByTestId('tab-rounds')).not.toBeInTheDocument();
    expect(screen.queryByTestId('tab-followups')).not.toBeInTheDocument();

    // Student schedule should be rendered
    await waitFor(() => {
      expect(screen.getByText('Aditi Rao')).toBeInTheDocument();
      expect(screen.getByText('Google LLC')).toBeInTheDocument();
    });

    // Student can confirm their own attendance
    expect(screen.getByTestId('confirm-attendance-btn-sched-001')).toBeInTheDocument();

    // Student CANNOT see staff-only actions like Notify, Mark Conducted, or Add Round
    expect(screen.queryByTestId('notify-btn-sched-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('conducted-btn-sched-001')).not.toBeInTheDocument();
    expect(screen.queryByTestId('add-round-btn-sched-001')).not.toBeInTheDocument();
  });
});
