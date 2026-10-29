import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { UserManagementPage } from '../pages/admin/UserManagementPage';
import { usersApi } from '../api/usersApi';
import { User, Role, PaginatedUsersResponse, PaginatedAuditLogsResponse } from '../types/admin';

let currentMockAuthUser: any = {
  id: 'admin-001',
  email: 'admin@gqt.local',
  full_name: 'System Admin',
  is_superuser: true,
  roles: ['ADMIN'],
};

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: currentMockAuthUser,
    isAuthenticated: !!currentMockAuthUser,
    isLoading: false,
    hasRole: (role: string) =>
      currentMockAuthUser?.is_superuser || currentMockAuthUser?.roles?.includes(role) || false,
    hasAnyRole: (roles: string[]) =>
      currentMockAuthUser?.is_superuser ||
      roles.some((r: string) => currentMockAuthUser?.roles?.includes(r)) ||
      false,
    login: vi.fn(),
    logout: vi.fn(),
    checkAuth: vi.fn(),
  }),
}));

vi.mock('../api/usersApi', () => ({
  usersApi: {
    listUsers: vi.fn(),
    getUser: vi.fn(),
    createUser: vi.fn(),
    updateUser: vi.fn(),
    updateUserStatus: vi.fn(),
    assignUserRoles: vi.fn(),
    listRoles: vi.fn(),
    getUserAuditLogs: vi.fn(),
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

const mockRoles: Role[] = [
  { id: 'r-1', code: 'ADMIN', name: 'System Administrator', description: 'Full system privileges', is_active: true },
  { id: 'r-2', code: 'PLACEMENT_HEAD', name: 'Placement Head', description: 'Placement director', is_active: true },
  { id: 'r-3', code: 'TRAINER', name: 'Placement Trainer', description: 'Technical trainer', is_active: true },
  { id: 'r-4', code: 'STUDENT', name: 'Enrolled Student', description: 'Student candidate', is_active: true },
];

const mockUsers: User[] = [
  {
    id: 'user-001',
    email: 'admin@gqt.local',
    first_name: 'System',
    last_name: 'Admin',
    full_name: 'System Admin',
    phone_number: '+91 99999 00000',
    is_active: true,
    is_staff: true,
    is_superuser: true,
    roles: ['ADMIN'],
    created_at: '2026-01-01T00:00:00Z',
    last_login: '2026-10-29T10:00:00Z',
  },
  {
    id: 'user-002',
    email: 'student.jane@gqt.local',
    first_name: 'Jane',
    last_name: 'Doe',
    full_name: 'Jane Doe',
    phone_number: '+91 98765 11111',
    is_active: true,
    is_staff: false,
    is_superuser: false,
    roles: ['STUDENT'],
    created_at: '2026-02-01T00:00:00Z',
    last_login: '2026-10-28T10:00:00Z',
  },
  {
    id: 'user-003',
    email: 'inactive.user@gqt.local',
    first_name: 'Bob',
    last_name: 'Inactive',
    full_name: 'Bob Inactive',
    phone_number: '',
    is_active: false,
    is_staff: false,
    is_superuser: false,
    roles: ['TRAINER'],
    created_at: '2026-03-01T00:00:00Z',
    last_login: null,
  },
];

const mockUsersResponse: PaginatedUsersResponse = {
  success: true,
  meta: {
    count: 3,
    total_pages: 1,
    current_page: 1,
    next: null,
    previous: null,
  },
  data: mockUsers,
};

const mockAuditResponse: PaginatedAuditLogsResponse = {
  success: true,
  meta: {
    count: 2,
    total_pages: 1,
    current_page: 1,
    next: null,
    previous: null,
  },
  data: [
    {
      id: 'aud-1',
      action: 'USER_CREATED',
      resource_type: 'accounts.User',
      resource_id: 'user-002',
      actor_email: 'admin@gqt.local',
      actor_name: 'System Admin',
      ip_address: '127.0.0.1',
      user_agent: 'Vitest Test Agent',
      correlation_id: 'corr-123',
      changes: { email: 'student.jane@gqt.local', roles: ['STUDENT'] },
      created_at: '2026-02-01T00:00:00Z',
    },
    {
      id: 'aud-2',
      action: 'USER_PROFILE_UPDATED',
      resource_type: 'accounts.User',
      resource_id: 'user-002',
      actor_email: 'admin@gqt.local',
      actor_name: 'System Admin',
      ip_address: '127.0.0.1',
      user_agent: 'Vitest Test Agent',
      correlation_id: 'corr-124',
      changes: { phone_number: { before: '', after: '+91 98765 11111' } },
      created_at: '2026-02-02T10:00:00Z',
    },
  ],
};

describe('UserManagementPage — Phase 15 Workstream 2 Verification', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = createTestQueryClient();
    currentMockAuthUser = {
      id: 'admin-001',
      email: 'admin@gqt.local',
      full_name: 'System Admin',
      is_superuser: true,
      roles: ['ADMIN'],
    };
    vi.mocked(usersApi.listUsers).mockResolvedValue(mockUsersResponse);
    vi.mocked(usersApi.listRoles).mockResolvedValue(mockRoles);
  });

  const renderComponent = (initialEntries = ['/admin/users']) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={initialEntries}>
          <Routes>
            <Route path="/admin/users" element={<UserManagementPage />} />
            <Route path="/access-denied" element={<div data-testid="access-denied-page">Access Denied</div>} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };

  it('renders user directory with user records, roles, and status badges', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('User & Role Administration')).toBeInTheDocument();
      expect(screen.getByText('student.jane@gqt.local')).toBeInTheDocument();
      expect(screen.getByText('Jane Doe')).toBeInTheDocument();
      expect(screen.getByText('inactive.user@gqt.local')).toBeInTheDocument();
    });

    // Check status badges
    expect(screen.getAllByText('Active').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Deactivated')).toBeInTheDocument();
  });

  it('filters users by search input keyword', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Jane Doe')).toBeInTheDocument();
    });

    const searchInput = screen.getByLabelText(/Search users/i);
    fireEvent.change(searchInput, { target: { value: 'Jane' } });

    await waitFor(() => {
      expect(usersApi.listUsers).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'Jane' })
      );
    });
  });

  it('filters users by role and status dropdowns', async () => {
    renderComponent();

    await waitFor(() => {
      expect(screen.getByLabelText(/Filter by role/i)).toBeInTheDocument();
    });

    // Filter by TRAINER role
    const roleSelect = screen.getByLabelText(/Filter by role/i);
    fireEvent.change(roleSelect, { target: { value: 'TRAINER' } });

    await waitFor(() => {
      expect(usersApi.listUsers).toHaveBeenCalledWith(
        expect.objectContaining({ role: 'TRAINER' })
      );
    });

    // Wait for status dropdown to be present and filter by inactive status
    await waitFor(() => {
      expect(screen.getByLabelText(/Filter by account status/i)).toBeInTheDocument();
    });
    const statusSelect = screen.getByLabelText(/Filter by account status/i);
    fireEvent.change(statusSelect, { target: { value: 'inactive' } });

    await waitFor(() => {
      expect(usersApi.listUsers).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'inactive' })
      );
    });
  });

  it('opens provision user account modal and submits valid creation payload', async () => {
    const newUser: User = {
      id: 'user-004',
      email: 'new.member@gqt.local',
      first_name: 'New',
      last_name: 'Member',
      full_name: 'New Member',
      phone_number: '+91 90000 11111',
      is_active: true,
      is_staff: false,
      is_superuser: false,
      roles: ['TRAINER'],
      created_at: '2026-10-29T10:00:00Z',
      last_login: null,
    };
    vi.mocked(usersApi.createUser).mockResolvedValue(newUser);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Provision User Account/i })).toBeInTheDocument();
    });

    // Open modal
    fireEvent.click(screen.getByRole('button', { name: /Provision User Account/i }));
    expect(screen.getByRole('heading', { name: 'Provision User Account' })).toBeInTheDocument();

    // Fill form
    fireEvent.change(screen.getByPlaceholderText('employee@gqt.local'), {
      target: { value: 'new.member@gqt.local' },
    });
    fireEvent.change(screen.getByPlaceholderText('Strong initial password'), {
      target: { value: 'SecureP@ssw0rd123!' },
    });
    fireEvent.change(screen.getByPlaceholderText('First name'), {
      target: { value: 'New' },
    });
    fireEvent.change(screen.getByPlaceholderText('Last name'), {
      target: { value: 'Member' },
    });

    // Click submit
    const submitBtn = screen.getByRole('button', { name: 'Provision Account' });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(usersApi.createUser).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'new.member@gqt.local',
          password: 'SecureP@ssw0rd123!',
          first_name: 'New',
          last_name: 'Member',
        })
      );
      expect(screen.getByText(/has been provisioned successfully/i)).toBeInTheDocument();
    });
  });

  it('opens edit profile modal and submits updated details', async () => {
    const updatedUser: User = {
      ...mockUsers[1]!,
      first_name: 'Janet',
      full_name: 'Janet Doe',
    };
    vi.mocked(usersApi.updateUser).mockResolvedValue(updatedUser);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('student.jane@gqt.local')).toBeInTheDocument();
    });

    // Click edit button for Jane
    const editBtn = screen.getByLabelText('Edit student.jane@gqt.local');
    fireEvent.click(editBtn);

    expect(screen.getByText('Edit User Profile')).toBeInTheDocument();

    // Change first name
    const firstNameInput = screen.getByDisplayValue('Jane');
    fireEvent.change(firstNameInput, { target: { value: 'Janet' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: 'Save Profile Changes' }));

    await waitFor(() => {
      expect(usersApi.updateUser).toHaveBeenCalledWith('user-002', {
        first_name: 'Janet',
        last_name: 'Doe',
        phone_number: '+91 98765 11111',
      });
      expect(screen.getByText(/updated successfully/i)).toBeInTheDocument();
    });
  });

  it('opens role assignment modal and synchronizes roles', async () => {
    vi.mocked(usersApi.assignUserRoles).mockResolvedValue({
      roles: ['STUDENT', 'TRAINER'],
    });

    renderComponent();

    await waitFor(() => {
      expect(screen.getByLabelText('Manage roles for student.jane@gqt.local')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Manage roles for student.jane@gqt.local'));

    expect(screen.getByText(/Manage Roles: Jane Doe/i)).toBeInTheDocument();

    // Submit synchronized roles
    fireEvent.click(screen.getByRole('button', { name: 'Synchronize Roles' }));

    await waitFor(() => {
      expect(usersApi.assignUserRoles).toHaveBeenCalledWith('user-002', {
        role_codes: ['STUDENT'],
      });
    });
  });

  it('opens account deactivation confirmation dialog and executes status mutation', async () => {
    const deactivatedUser: User = {
      ...mockUsers[1]!,
      is_active: false,
    };
    vi.mocked(usersApi.updateUserStatus).mockResolvedValue(deactivatedUser);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByLabelText('Deactivate student.jane@gqt.local')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('Deactivate student.jane@gqt.local'));

    expect(screen.getByText('Confirm Account Deactivation')).toBeInTheDocument();
    expect(screen.getByText('Immediate Session Revocation')).toBeInTheDocument();

    // Confirm
    fireEvent.click(screen.getByRole('button', { name: 'Confirm Deactivation' }));

    await waitFor(() => {
      expect(usersApi.updateUserStatus).toHaveBeenCalledWith('user-002', {
        is_active: false,
      });
    });
  });

  it('opens security audit history modal and displays audit timeline with actor details', async () => {
    vi.mocked(usersApi.getUserAuditLogs).mockResolvedValue(mockAuditResponse);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByLabelText('View audit logs for student.jane@gqt.local')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByLabelText('View audit logs for student.jane@gqt.local'));

    await waitFor(() => {
      expect(screen.getByText(/Security Audit Trail/i)).toBeInTheDocument();
      expect(screen.getByText('USER_CREATED')).toBeInTheDocument();
      expect(screen.getByText('USER_PROFILE_UPDATED')).toBeInTheDocument();
      expect(screen.getByText(/corr-123/i)).toBeInTheDocument();
    });
  });

  it('redirects non-admin accounts to /access-denied without querying user APIs', async () => {
    currentMockAuthUser = {
      id: 'student-001',
      email: 'student@gqt.local',
      full_name: 'Student User',
      is_superuser: false,
      roles: ['STUDENT'],
    };

    renderComponent();

    await waitFor(() => {
      expect(screen.getByTestId('access-denied-page')).toBeInTheDocument();
    });

    expect(usersApi.listUsers).not.toHaveBeenCalled();
    expect(usersApi.listRoles).not.toHaveBeenCalled();
  });
});

