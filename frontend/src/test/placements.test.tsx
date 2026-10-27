import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PlacementWorkspacePage } from '../pages/placements/PlacementWorkspacePage';
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
  total_results: 12,
  selected_count: 8,
  rejected_count: 2,
  waiting_list_count: 1,
  hold_count: 1,
  total_offers: 6,
  offers_accepted: 4,
  offers_declined: 1,
  offers_pending: 1,
  total_joined: 3,
  total_deferred: 1,
  total_not_joined: 0,
};

const mockJobs = [
  {
    id: 'job-001',
    title: 'Associate Software Engineer',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sarah Jenkins',
    status: 'APPROVED',
  },
];

const mockCandidateStatuses = [
  {
    id: 'place-001',
    job_requirement: 'job-001',
    job_title: 'Associate Software Engineer',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    student: 'stud-001',
    student_roll: '1GQ22CS001',
    student_name: 'Aarav Sharma',
    student_email: 'aarav.sharma@gqt.edu',
    status: 'SELECTED',
    status_display: 'Selected',
    designation_offered: 'Junior SDE',
    offered_ctc: '850000.00',
    work_location: 'Bangalore Campus',
    remarks: 'Outstanding coding performance',
    has_offer_letter: true,
    offer_letter_id: 'offer-001',
    acceptance_status: 'PENDING_RESPONSE',
    joining_status: 'NOT_APPLICABLE',
    status_updated_at: '2026-10-27T09:00:00Z',
    status_updated_by_name: 'Placement Officer',
    created_at: '2026-10-27T09:00:00Z',
    offer_letter: {
      id: 'offer-001',
      file_name: 'techcorp_offer_aarav.pdf',
      file_size_bytes: 102400,
      sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      version_number: 1,
      is_active: true,
      issued_at: '2026-10-27T09:15:00Z',
      issued_by_name: 'Placement Officer',
      acceptance_deadline: '2026-11-10',
      acceptance_status: 'PENDING_RESPONSE',
      acceptance_status_display: 'Pending Candidate Response',
      accepted_at: null,
      acceptance_source: 'STUDENT_PORTAL',
      student_decision_notes: '',
      joining_status: 'NOT_APPLICABLE',
      joining_status_display: 'Not Applicable',
      expected_joining_date: '2026-12-01',
      actual_joining_date: null,
      deferred_joining_date: null,
      joining_location: 'Bangalore Campus',
      employee_id_assigned: '',
      joining_notes: '',
      joining_verified_at: null,
      download_url: '/api/v1/placements/offers/offer-001/download/',
      created_at: '2026-10-27T09:15:00Z',
    },
  },
  {
    id: 'place-002',
    job_requirement: 'job-001',
    job_title: 'Associate Software Engineer',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    student: 'stud-002',
    student_roll: '1GQ22CS002',
    student_name: 'Priya Patel',
    student_email: 'priya.patel@gqt.edu',
    status: 'HOLD',
    status_display: 'Hold',
    designation_offered: '',
    offered_ctc: null,
    work_location: '',
    remarks: 'Awaiting headcount confirmation',
    has_offer_letter: false,
    offer_letter_id: null,
    acceptance_status: null,
    joining_status: null,
    status_updated_at: '2026-10-27T09:00:00Z',
    status_updated_by_name: 'Placement Officer',
    created_at: '2026-10-27T09:00:00Z',
  },
];

const mockOffers = [
  mockCandidateStatuses[0]!.offer_letter!,
];

const mockIntakes = [
  {
    id: 'intake-001',
    job_requirement: 'job-001',
    job_title: 'Associate Software Engineer',
    company: 'comp-001',
    company_name: 'TechCorp Global Ltd',
    hr_contact: 'hr-001',
    hr_contact_name: 'Sarah Jenkins',
    result_reference_code: 'RES-20261027-A1B2',
    source: 'EMAIL',
    source_display: 'Corporate HR Email',
    received_at: '2026-10-27T09:00:00Z',
    total_results: 2,
    selected_count: 1,
    rejected_count: 0,
    waiting_list_count: 0,
    hold_count: 1,
    notes: 'Official drive result roster',
    created_at: '2026-10-27T09:00:00Z',
    created_by_name: 'Placement Officer',
  },
];

const mockParticipatingCandidates = [
  {
    student_id: 'stud-001',
    roll_number: '1GQ22CS001',
    student_name: 'Aarav Sharma',
    institutional_email: 'aarav.sharma@gqt.edu',
    department: 'Computer Science',
    degree: 'B.Tech',
    cgpa: 8.8,
    existing_placement_status: 'SELECTED',
  },
];

describe('Placement Management Workspace (Workflow Steps 36–41)', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();

    // Default mock responses
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-officer',
            email: 'officer@gqt.internal',
            full_name: 'Placement Officer',
            roles: ['PLACEMENT_OFFICER', 'ADMIN'],
            role_assignments: [
              { id: 'ra-1', role: { code: 'PLACEMENT_OFFICER', name: 'Placement Officer' }, is_active: true },
            ],
            is_active: true,
            is_staff: true,
            is_superuser: true,
          },
        });
      }
      if (url.includes('/placements/kpis/')) {
        return Promise.resolve({ data: mockKPIs });
      }
      if (url.includes('/placements/statuses/')) {
        return Promise.resolve({ data: mockCandidateStatuses });
      }
      if (url.includes('/placements/offers/')) {
        return Promise.resolve({ data: mockOffers });
      }
      if (url.includes('/placements/intakes/')) {
        return Promise.resolve({ data: mockIntakes });
      }
      if (url.includes('/candidates/')) {
        return Promise.resolve({ data: mockParticipatingCandidates });
      }
      if (url.includes('/jobs/')) {
        return Promise.resolve({ data: { data: mockJobs, results: mockJobs } });
      }
      if (url.includes('/placements/my-placements/')) {
        return Promise.resolve({ data: mockCandidateStatuses });
      }
      return Promise.resolve({ data: [] });
    });

    (apiClient.post as any).mockImplementation((url: string) => {
      if (url.includes('/placements/intakes/')) {
        return Promise.resolve({ data: mockIntakes[0] });
      }
      if (url.includes('/update-status/')) {
        return Promise.resolve({ data: { ...mockCandidateStatuses[0], status: 'SELECTED' } });
      }
      if (url.includes('/notify/')) {
        return Promise.resolve({
          data: {
            id: 'notif-001',
            recipient_email: 'aarav.sharma@gqt.edu',
            status: 'SENT',
            channel: 'EMAIL',
          },
        });
      }
      if (url.includes('/upload-offer/')) {
        return Promise.resolve({ data: mockOffers[0] });
      }
      if (url.includes('/respond/')) {
        return Promise.resolve({ data: { ...mockOffers[0], acceptance_status: 'ACCEPTED' } });
      }
      if (url.includes('/verify-joining/')) {
        return Promise.resolve({ data: { ...mockOffers[0], joining_status: 'JOINED' } });
      }
      return Promise.resolve({ data: {} });
    });
  });

  const renderWithProviders = (ui: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>{ui}</MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

  it('renders placement workspace with KPI summary banner and candidate list', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    expect(await screen.findByText('Placement Management')).toBeInTheDocument();
    expect(screen.getByText('Phase 8: Placement Management & Tracking (Workflow Steps 36–41)')).toBeInTheDocument();

    // Verify KPI Cards
    expect(await screen.findByText('Total Results')).toBeInTheDocument();
    expect(screen.getAllByText('Selected').length).toBeGreaterThan(0);
    expect(screen.getByText('Offers Issued')).toBeInTheDocument();

    // Verify Candidate Table
    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();
    expect(screen.getByText('Priya Patel')).toBeInTheDocument();
    expect(screen.getAllByText('TechCorp Global Ltd').length).toBeGreaterThan(0);
  });

  it('displays Candidate Statuses tab with status badges and update actions (Step 37)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();

    // Check Update Status button exists
    const updateButtons = screen.getAllByRole('button', { name: /Update Status/i });
    expect(updateButtons.length).toBeGreaterThan(0);

    // Open Update Status Modal
    fireEvent.click(updateButtons[0]!);
    expect(await screen.findByText('Update Candidate Status (Step 37)')).toBeInTheDocument();
  });

  it('allows opening the Student Notification modal (Step 38)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();

    const notifyButtons = screen.getAllByTitle(/Notify Student/i);
    expect(notifyButtons.length).toBeGreaterThan(0);

    fireEvent.click(notifyButtons[0]!);
    expect(await screen.findByText('Notify Candidate (Step 38)')).toBeInTheDocument();
    expect(screen.getByText('Direct Institutional Email')).toBeInTheDocument();
  });

  it('allows staff to upload an official offer letter PDF (Step 39)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    expect(await screen.findByText('Aarav Sharma')).toBeInTheDocument();

    const offerButton = screen.getByTitle('Upload Official Offer Letter (Step 39)');
    fireEvent.click(offerButton);

    expect(await screen.findByText('Upload Official Offer Letter (Step 39)')).toBeInTheDocument();
    expect(screen.getByText(/Offer Letter PDF Document \* \(Max 5MB\)/i)).toBeInTheDocument();
  });

  it('switches to Offer Letters & Acceptance tab and shows response status (Step 40)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    const offersTab = await screen.findByRole('button', { name: /Offer Letters & Acceptance/i });
    fireEvent.click(offersTab);

    expect(await screen.findByText('Offer Letters & Response Lifecycle (Steps 39 & 40)')).toBeInTheDocument();
    expect(screen.getByText('techcorp_offer_aarav.pdf')).toBeInTheDocument();
    expect(screen.getByText('Pending Candidate Response')).toBeInTheDocument();

    // Record response button
    const recordResponseBtn = screen.getByRole('button', { name: /Record Response/i });
    fireEvent.click(recordResponseBtn);

    expect(await screen.findByText('Record Offer Decision (Step 40)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Accept Offer/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Decline Offer/i })).toBeInTheDocument();
  });

  it('switches to Joining Verification tab and verifies joining status (Step 41)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    const joiningTab = await screen.findByRole('button', { name: /Joining Verification/i });
    fireEvent.click(joiningTab);

    expect(await screen.findByText('Joining Status & Candidate Reporting (Step 41)')).toBeInTheDocument();

    const verifyBtn = screen.getByRole('button', { name: /Verify Status/i });
    fireEvent.click(verifyBtn);

    expect(await screen.findByText('Verify Candidate Joining (Step 41)')).toBeInTheDocument();
    expect(screen.getByText('Joining Outcome *')).toBeInTheDocument();
  });

  it('switches to Intake Batches tab and lists historical final result batches (Step 36)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    const intakesTab = await screen.findByRole('button', { name: /Intake Batches/i });
    fireEvent.click(intakesTab);

    expect(await screen.findByText('Final Result Ingestion Batches (Step 36)')).toBeInTheDocument();
    expect(screen.getByText('RES-20261027-A1B2')).toBeInTheDocument();
    expect(screen.getByText('Corporate HR Email')).toBeInTheDocument();
  });

  it('opens Ingest Final Results modal and populates participating candidates (Step 36)', async () => {
    renderWithProviders(<PlacementWorkspacePage />);

    const ingestBtn = await screen.findByRole('button', { name: /Ingest Final Results/i });
    fireEvent.click(ingestBtn);

    expect(await screen.findByText('Ingest Final Results from Corporate HR (Step 36)')).toBeInTheDocument();
    expect(screen.getByText('Approved Recruitment Drive *')).toBeInTheDocument();
  });

  it('isolates student view and hides staff-only intake and evaluation controls', async () => {
    // Override user mock as STUDENT role
    (apiClient.get as any).mockImplementation((url: string) => {
      if (url.includes('/auth/me/')) {
        return Promise.resolve({
          data: {
            id: 'user-student',
            email: 'aarav.sharma@gqt.edu',
            full_name: 'Aarav Sharma',
            roles: ['STUDENT'],
            role_assignments: [
              { id: 'ra-s', role: { code: 'STUDENT', name: 'Student' }, is_active: true },
            ],
            is_active: true,
            is_staff: false,
            is_superuser: false,
          },
        });
      }
      if (url.includes('/placements/my-placements/')) {
        return Promise.resolve({ data: [mockCandidateStatuses[0]] });
      }
      return Promise.resolve({ data: [] });
    });

    renderWithProviders(<PlacementWorkspacePage />);

    expect(await screen.findByText('My Placement Opportunities & Offers')).toBeInTheDocument();
    expect(screen.getByText('Candidate Self-Service')).toBeInTheDocument();

    // Staff intake controls must be absent
    expect(screen.queryByRole('button', { name: /Ingest Final Results/i })).not.toBeInTheDocument();
    expect(screen.queryByText('Total Results')).not.toBeInTheDocument();
  });
});
