import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CreativeDirectoryPage } from '../pages/creatives/CreativeDirectoryPage';
import { CreativeDetailPage } from '../pages/creatives/CreativeDetailPage';
import { CreativeReviewQueuePage } from '../pages/creatives/CreativeReviewQueuePage';
import { DesignerWorkQueuePage } from '../pages/creatives/DesignerWorkQueuePage';
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

const mockActiveVersion = {
  id: 'ver-1',
  version_number: 1,
  file: 'http://localhost:8000/media/creatives/flyer_v1.png',
  file_name: 'wipro_cloud_flyer_v1.png',
  file_size_bytes: 524288,
  mime_type: 'image/png',
  sha256_hash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
  width_px: 1200,
  height_px: 1800,
  status: 'IN_REVIEW',
  status_display: 'In Review',
  designer_notes: 'Initial high-res flyer with verified corporate logo and QR code.',
  is_approved: false,
  uploaded_by: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
  created_at: '2026-10-26T10:30:00Z',
  checklist_progress: {
    total: 4,
    verified: 2,
    percent: 50,
    all_verified: false,
  },
  checklist_items: [
    {
      id: 'item-1',
      item_code: 'FLYER_ACCURACY',
      title: 'Flyer Content & JD Accuracy',
      description: 'Verify job title, eligibility criteria, compensation package, drive date, and venue match the approved JD.',
      is_mandatory: true,
      status: 'VERIFIED',
      verified_by: { id: 'head-1', full_name: 'Placement Head User' },
      verified_at: '2026-10-26T11:00:00Z',
      remarks: 'All package and eligibility criteria verified against approved JD.',
    },
    {
      id: 'item-2',
      item_code: 'OFFICIAL_LOGO',
      title: 'Corporate & Institutional Branding',
      description: 'Verify high-resolution official employer logo is used and GQT institutional brand guidelines are followed.',
      is_mandatory: true,
      status: 'VERIFIED',
      verified_by: { id: 'head-1', full_name: 'Placement Head User' },
      verified_at: '2026-10-26T11:05:00Z',
      remarks: 'Wipro high-res SVG/vector logo and GQT branding correct.',
    },
    {
      id: 'item-3',
      item_code: 'QR_CODE',
      title: 'QR Code Functionality & Contrast',
      description: 'Verify QR code is high-contrast, scannable by mobile devices, and resolves to the designated registration URL.',
      is_mandatory: true,
      status: 'PENDING',
      verified_by: null,
      verified_at: null,
      remarks: '',
    },
    {
      id: 'item-4',
      item_code: 'REGISTRATION_LINK_AND_CONTACTS',
      title: 'Registration Link & Placement Cell Contacts',
      description: 'Verify registration URL is legible in text, deadline date is clear, and placement cell contact details are correct.',
      is_mandatory: true,
      status: 'PENDING',
      verified_by: null,
      verified_at: null,
      remarks: '',
    },
  ],
};

const mockCreativeRequest = {
  id: 'creative-req-1',
  title: 'Cloud Engineer Campus Flyer 2026',
  job_requirement: 'job-1',
  job_title: 'Associate Cloud Engineer',
  company_name: 'Wipro Limited',
  job_location: 'Bangalore',
  job_salary_display: '₹6.00L - ₹8.50L PA',
  job_openings_count: 10,
  job_registration_deadline: '2026-12-31T23:59:59Z',
  job_interview_date: '2027-01-15',
  deliverable_type: 'FLYER',
  deliverable_type_display: 'Promotional Flyer',
  status: 'REVIEW_PENDING',
  status_display: 'Under Review',
  priority: 'HIGH',
  brief: 'Create campus recruitment flyer highlighting 10 openings in Bangalore cloud team.',
  target_audience: 'B.Tech/MCA 2026 Batch with 60%+ aggregate',
  registration_url: 'https://gqt.edu/register/wipro-2026',
  qr_code_target_url: 'https://gqt.edu/register/wipro-2026?src=qr',
  contact_email: 'placement@gqt.edu',
  contact_phone: '+91 9876543210',
  requested_by: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
  created_by: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
  assigned_designer: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
  deadline: '2026-11-15T18:00:00Z',
  created_at: '2026-10-26T10:00:00Z',
  updated_at: '2026-10-26T11:00:00Z',
  versions_count: 1,
  active_version: mockActiveVersion,
  versions: [mockActiveVersion],
  decisions: [
    {
      id: 'dec-1',
      action: 'CREATED',
      actor: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
      version_number: null,
      notes: 'Initial request dispatched to graphic design pool.',
      created_at: '2026-10-26T10:00:00Z',
    },
    {
      id: 'dec-2',
      action: 'SUBMITTED',
      actor: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
      version_number: 1,
      notes: 'v1 uploaded and submitted for 4-point design verification checklist audit.',
      created_at: '2026-10-26T10:30:00Z',
    },
  ],
};

describe('Frontend Creative Studio & Promotional Assets Suite (Phase 4 / Steps 8-9)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Creative Directory with KPI metrics and requests table', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'officer-1',
            email: 'officer@gqt.local',
            roles: ['PLACEMENT_OFFICER'],
            full_name: 'Officer User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url === '/creatives/requests/') {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'creative-req-1',
                title: 'Cloud Engineer Campus Flyer 2026',
                job_requirement: 'job-1',
                job_title: 'Associate Cloud Engineer',
                company_name: 'Wipro Limited',
                deliverable_type: 'FLYER',
                deliverable_type_display: 'Promotional Flyer',
                status: 'REVIEW_PENDING',
                status_display: 'Under Review',
                priority: 'HIGH',
                assigned_designer: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
                requested_by: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
                deadline: '2026-11-15T18:00:00Z',
                versions_count: 1,
                active_version_number: 1,
                active_version_status: 'IN_REVIEW',
                active_version_checklist_progress: {
                  total: 4,
                  verified: 2,
                  percent: 50,
                  all_verified: false,
                },
                is_archived: false,
                created_at: '2026-10-26T10:00:00Z',
                updated_at: '2026-10-26T11:00:00Z',
              },
            ],
          },
        });
      }
      if (url === '/creatives/requests/metrics/') {
        return Promise.resolve({
          data: {
            total_active: 8,
            in_production: 3,
            review_pending: 2,
            changes_requested: 1,
            approved: 2,
            urgent_deadlines: 1,
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives']}>
            <CreativeDirectoryPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    // Verify Title & Metrics
    await waitFor(() => {
      expect(screen.getByText(/Creative Studio & Promotional Assets/i)).toBeInTheDocument();
      expect(screen.getByText('Cloud Engineer Campus Flyer 2026')).toBeInTheDocument();
      expect(screen.getByText('Wipro Limited')).toBeInTheDocument();
      expect(screen.getByText('Aditi Sharma')).toBeInTheDocument();
    });
  });

  it('renders Creative Detail workspace with authoritative 4-point design verification checklist (Step 9)', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'head-1',
            email: 'head@gqt.local',
            roles: ['PLACEMENT_HEAD'],
            full_name: 'Placement Head User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url === '/creatives/requests/creative-req-1/') {
        return Promise.resolve({
          data: mockCreativeRequest,
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives/creative-req-1']}>
            <Routes>
              <Route path="/creatives/:id" element={<CreativeDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Cloud Engineer Campus Flyer 2026')).toBeInTheDocument();
      expect(screen.getByText(/4-Point Design Verification Checklist/i)).toBeInTheDocument();
      // Verify all 4 checklist points from authoritative Step 9
      expect(screen.getByText('Flyer Content & JD Accuracy')).toBeInTheDocument();
      expect(screen.getByText('Corporate & Institutional Branding')).toBeInTheDocument();
      expect(screen.getByText('QR Code Functionality & Contrast')).toBeInTheDocument();
      expect(screen.getByText('Registration Link & Placement Cell Contacts')).toBeInTheDocument();
    });
  });

  it('disables Placement Head Sign-Off button when checklist criteria are incomplete (Step 9 Gate)', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'head-1',
            email: 'head@gqt.local',
            roles: ['PLACEMENT_HEAD'],
            full_name: 'Placement Head User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url === '/creatives/requests/creative-req-1/') {
        return Promise.resolve({
          data: mockCreativeRequest, // active_version has only 2/4 verified
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives/creative-req-1']}>
            <Routes>
              <Route path="/creatives/:id" element={<CreativeDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Cloud Engineer Campus Flyer 2026')).toBeInTheDocument();
    });

    // Placement Head Sign-off button should be rendered and disabled
    const signOffButton = screen.getByRole('button', { name: /Sign Off & Approve/i });
    expect(signOffButton).toBeDisabled();
    expect(signOffButton).toHaveAttribute('title', expect.stringContaining('Sign-off is locked'));
  });

  it('renders Creative Review Queue with dual tabs for Checklist Audits and Placement Head Sign-Offs', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'head-1',
            email: 'head@gqt.local',
            roles: ['PLACEMENT_HEAD'],
            full_name: 'Placement Head User',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url.startsWith('/creatives/requests/pending-review/')) {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'creative-req-1',
                title: 'Cloud Engineer Campus Flyer 2026',
                job_requirement: 'job-1',
                job_title: 'Associate Cloud Engineer',
                company_name: 'Wipro Limited',
                deliverable_type: 'FLYER',
                deliverable_type_display: 'Promotional Flyer',
                status: 'REVIEW_PENDING',
                status_display: 'Under Review',
                priority: 'HIGH',
                assigned_designer: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
                requested_by: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
                deadline: '2026-11-15T18:00:00Z',
                versions_count: 1,
                active_version_number: 1,
                active_version_status: 'IN_REVIEW',
                active_version_checklist_progress: {
                  total: 4,
                  verified: 2,
                  percent: 50,
                  all_verified: false,
                },
                is_archived: false,
                created_at: '2026-10-26T10:00:00Z',
                updated_at: '2026-10-26T11:00:00Z',
              },
            ],
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives/queue']}>
            <CreativeReviewQueuePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Creative Review & Approval Queues/i)).toBeInTheDocument();
      expect(screen.getByText(/Checklist Audits Queue/i)).toBeInTheDocument();
      expect(screen.getByText(/Placement Head Sign-Off Queue/i)).toBeInTheDocument();
      expect(screen.getByText('Cloud Engineer Campus Flyer 2026')).toBeInTheDocument();
    });
  });

  it('renders Designer Work Queue workbench for graphic designers', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'designer-1',
            email: 'designer@gqt.local',
            roles: ['CREATIVE_DESIGNER'],
            full_name: 'Aditi Sharma',
            is_active: true,
            is_staff: true,
            is_superuser: false,
          },
        });
      }
      if (url === '/creatives/requests/designer-queue/') {
        return Promise.resolve({
          data: {
            success: true,
            meta: { count: 1, total_pages: 1, current_page: 1, next: null, previous: null },
            data: [
              {
                id: 'creative-req-1',
                title: 'Cloud Engineer Campus Flyer 2026',
                job_requirement: 'job-1',
                job_title: 'Associate Cloud Engineer',
                company_name: 'Wipro Limited',
                deliverable_type: 'FLYER',
                deliverable_type_display: 'Promotional Flyer',
                status: 'IN_PRODUCTION',
                status_display: 'In Production',
                priority: 'HIGH',
                assigned_designer: { id: 'designer-1', email: 'designer@gqt.local', full_name: 'Aditi Sharma', role: 'CREATIVE_DESIGNER' },
                requested_by: { id: 'officer-1', email: 'officer@gqt.local', full_name: 'Officer User', role: 'PLACEMENT_OFFICER' },
                deadline: '2026-11-15T18:00:00Z',
                versions_count: 0,
                active_version: null,
                is_archived: false,
                created_at: '2026-10-26T10:00:00Z',
                updated_at: '2026-10-26T11:00:00Z',
              },
            ],
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives/my-tasks']}>
            <DesignerWorkQueuePage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Designer Workbench/i)).toBeInTheDocument();
      expect(screen.getByText('Cloud Engineer Campus Flyer 2026')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Open Workspace/i })).toBeInTheDocument();
    });
  });

  it('denies Student role access to creative routes via ProtectedRoute', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/auth/me/') {
        return Promise.resolve({
          data: {
            id: 'student-1',
            email: 'student@gqt.local',
            roles: ['STUDENT'],
            full_name: 'Student Candidate',
            is_active: true,
            is_staff: false,
            is_superuser: false,
          },
        });
      }
      return Promise.reject(new Error(`Unhandled GET url: ${url}`));
    });

    render(
      <QueryClientProvider client={createTestQueryClient()}>
        <AuthProvider>
          <MemoryRouter initialEntries={['/creatives']}>
            <Routes>
              <Route
                path="/creatives"
                element={
                  <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'CREATIVE_DESIGNER']}>
                    <CreativeDirectoryPage />
                  </ProtectedRoute>
                }
              />
              <Route path="/access-denied" element={<div>Access Denied To Students</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Access Denied To Students')).toBeInTheDocument();
    });
  });
});
