import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { LoginPage } from '../pages/auth/LoginPage';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { AuthProvider } from '../context/AuthContext';
import { apiClient } from '../lib/apiClient';

// Mock apiClient
vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Frontend Authentication Suite (Phase 1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('renders login page with official branding, inputs, and accessible labels', () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: null });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Work Email Address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password$/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    expect(screen.getByText(/Forgot password\?/i)).toBeInTheDocument();
  });

  it('displays client-side validation errors when invalid input is submitted', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: null });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/Please enter a valid email address/i)).toBeInTheDocument();
      expect(screen.getByText(/Password is required/i)).toBeInTheDocument();
    });
  });

  it('never stores credentials or tokens in localStorage or sessionStorage', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({ data: null });
    vi.mocked(apiClient.post).mockResolvedValueOnce({
      data: {
        user: {
          id: 'test-uuid',
          email: 'student@gqt.local',
          full_name: 'Jane Doe',
          roles: ['STUDENT'],
        },
      },
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    fireEvent.change(screen.getByLabelText(/Work Email Address/i), {
      target: { value: 'student@gqt.local' },
    });
    fireEvent.change(screen.getByLabelText(/^Password$/i), {
      target: { value: 'SecretPassword123!' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Sign In/i }));

    await waitFor(() => {
      expect(apiClient.post).toHaveBeenCalledWith('/auth/login/', {
        email: 'student@gqt.local',
        password: 'SecretPassword123!',
      });
    });

    // Verification: Zero credentials in web storage
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('password')).toBeNull();
    expect(sessionStorage.getItem('token')).toBeNull();
  });

  it('redirects unauthenticated users to /login when attempting to access ProtectedRoute', async () => {
    vi.mocked(apiClient.get).mockRejectedValueOnce(new Error('Unauthenticated'));

    render(
      <MemoryRouter initialEntries={['/protected']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <div>Secret Protected Data</div>
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<div>Login Screen Destination</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Login Screen Destination')).toBeInTheDocument();
      expect(screen.queryByText('Secret Protected Data')).not.toBeInTheDocument();
    });
  });

  it('redirects to /access-denied when user lacks required role', async () => {
    vi.mocked(apiClient.get).mockResolvedValueOnce({
      data: {
        id: 'user-id',
        email: 'student@gqt.local',
        full_name: 'Student User',
        roles: ['STUDENT'],
        is_superuser: false,
      },
    });

    render(
      <MemoryRouter initialEntries={['/admin-only']}>
        <AuthProvider>
          <Routes>
            <Route
              path="/admin-only"
              element={
                <ProtectedRoute requiredRoles={['ADMIN']}>
                  <div>Admin Secret Area</div>
                </ProtectedRoute>
              }
            />
            <Route path="/access-denied" element={<div>Access Denied Screen</div>} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Access Denied Screen')).toBeInTheDocument();
      expect(screen.queryByText('Admin Secret Area')).not.toBeInTheDocument();
    });
  });
});
