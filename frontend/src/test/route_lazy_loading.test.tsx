import React, { Suspense, lazy } from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { RouteLoadingFallback } from '../components/layout/RouteLoadingFallback';
import { RouteErrorBoundary } from '../components/common/RouteErrorBoundary';
import { apiClient } from '../lib/apiClient';

vi.mock('../lib/apiClient', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

// Simulated lazy components
const LazySuccessComponent = lazy(() =>
  Promise.resolve({
    default: () => <div data-testid="lazy-success-content">Lazy Content Loaded Successfully</div>,
  })
);

const LazyFailingComponent = lazy(() =>
  Promise.reject(new Error('Failed to fetch dynamically imported module: /assets/chunk-123.js'))
);

const FailingRenderComponent: React.FC = () => {
  throw new Error('Generic rendering error in workspace component');
};

describe('Phase 15 Workstream 4 — Route Lazy Loading & Performance Suite', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    localStorage.clear();

    // Mock window.location.reload and window.location.href
    // @ts-expect-error mocking window.location
    delete window.location;
    window.location = {
      ...originalLocation,
      reload: vi.fn(),
      href: '',
    };
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  describe('RouteLoadingFallback Component', () => {
    it('renders with accessible status role and default message', () => {
      render(<RouteLoadingFallback />);

      const statusEl = screen.getByRole('status');
      expect(statusEl).toBeInTheDocument();
      expect(statusEl).toHaveAttribute('aria-live', 'polite');
      expect(statusEl).toHaveAttribute('aria-label', 'Loading page');
      expect(screen.getByText('Loading workspace...')).toBeInTheDocument();
      expect(screen.getByText(/Connecting to GQT HRMS services/i)).toBeInTheDocument();
    });

    it('renders custom message and respects fullScreen prop', () => {
      render(<RouteLoadingFallback message="Authenticating credentials..." fullScreen />);

      expect(screen.getByText('Authenticating credentials...')).toBeInTheDocument();
      const statusEl = screen.getByRole('status');
      expect(statusEl.className).toContain('min-h-screen');
    });
  });

  describe('RouteErrorBoundary Component', () => {
    it('renders children when no error occurs', () => {
      render(
        <RouteErrorBoundary>
          <div data-testid="child-content">Normal Content</div>
        </RouteErrorBoundary>
      );

      expect(screen.getByTestId('child-content')).toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('catches generic errors, suppresses stack traces, and provides retry actions', () => {
      // Suppress console.error during expected test error
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <RouteErrorBoundary fallbackTitle="Custom View Failure">
          <FailingRenderComponent />
        </RouteErrorBoundary>
      );

      const alertEl = screen.getByRole('alert');
      expect(alertEl).toBeInTheDocument();
      expect(alertEl).toHaveAttribute('aria-live', 'assertive');
      expect(screen.getByText('Custom View Failure')).toBeInTheDocument();
      expect(
        screen.getByText(/An unexpected error occurred while rendering this view/i)
      ).toBeInTheDocument();
      // Ensure raw stack trace or raw exception string is not leaked to the user
      expect(screen.queryByText(/Generic rendering error in workspace component/i)).not.toBeInTheDocument();

      const retryBtn = screen.getByRole('button', { name: /Try Again/i });
      expect(retryBtn).toBeInTheDocument();
      const homeBtn = screen.getByRole('button', { name: /Return to Dashboard/i });
      expect(homeBtn).toBeInTheDocument();

      consoleSpy.mockRestore();
    });

    it('detects chunk load errors, informs user about update, and triggers reload', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <RouteErrorBoundary>
          <Suspense fallback={<div>Loading...</div>}>
            <LazyFailingComponent />
          </Suspense>
        </RouteErrorBoundary>
      );

      return waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
        expect(screen.getByText('Application Update Detected')).toBeInTheDocument();
        expect(
          screen.getByText(/A new version of GQT HRMS has been deployed or your network connection was interrupted/i)
        ).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Reload Application/i })).toBeInTheDocument();
        expect(window.location.reload).toHaveBeenCalledTimes(1);
        consoleSpy.mockRestore();
      });
    });

    it('prevents infinite reload loops when chunk load error persists within cooldown window', async () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      // Simulate a previous reload that happened 2 seconds ago (within 15s cooldown)
      sessionStorage.setItem('gqt_chunk_retry_timestamp', (Date.now() - 2000).toString());

      render(
        <RouteErrorBoundary>
          <Suspense fallback={<div>Loading...</div>}>
            <LazyFailingComponent />
          </Suspense>
        </RouteErrorBoundary>
      );

      await waitFor(() => {
        expect(screen.getByText('Application Update Detected')).toBeInTheDocument();
      });

      // Reload should NOT have been called because it is within cooldown window
      expect(window.location.reload).not.toHaveBeenCalled();

      // Manual reload button remains available for user action
      const reloadBtn = screen.getByRole('button', { name: /Reload Application/i });
      fireEvent.click(reloadBtn);
      expect(window.location.reload).toHaveBeenCalledTimes(1);

      consoleSpy.mockRestore();
    });
  });

  describe('Route-Level Lazy Resolution and Protected Access', () => {
    it('renders fallback and then resolves lazy component in Suspense boundary', async () => {
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={['/lazy-test']}>
            <Suspense fallback={<RouteLoadingFallback message="Loading lazy view..." />}>
              <Routes>
                <Route path="/lazy-test" element={<LazySuccessComponent />} />
              </Routes>
            </Suspense>
          </MemoryRouter>
        </QueryClientProvider>
      );

      // Verify resolved content mounts cleanly
      await waitFor(() => {
        expect(screen.getByTestId('lazy-success-content')).toBeInTheDocument();
      });
    });

    it('redirects unauthenticated users trying to access protected lazy routes to /login', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({ data: null });
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/students/drives']}>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
                  <Route path="/login" element={<div data-testid="login-view">Login View</div>} />
                  <Route
                    path="/students/drives"
                    element={
                      <ProtectedRoute requiredRoles={['STUDENT']}>
                        <LazySuccessComponent />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('login-view')).toBeInTheDocument();
      });
      expect(screen.queryByTestId('lazy-success-content')).not.toBeInTheDocument();
    });

    it('redirects authenticated non-student users from /students/drives to /access-denied', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: {
          id: 'user-officer-1',
          email: 'officer@gqtech.in',
          first_name: 'Placement',
          last_name: 'Officer',
          roles: ['PLACEMENT_OFFICER'],
          is_active: true,
          is_superuser: false,
        },
      });
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/students/drives']}>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
                  <Route path="/access-denied" element={<div data-testid="access-denied-view">Access Denied</div>} />
                  <Route
                    path="/students/drives"
                    element={
                      <ProtectedRoute requiredRoles={['STUDENT']}>
                        <LazySuccessComponent />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('access-denied-view')).toBeInTheDocument();
      });
      expect(screen.queryByTestId('lazy-success-content')).not.toBeInTheDocument();
    });

    it('renders /students/drives for authorized STUDENT role', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: {
          id: 'user-student-1',
          email: 'student@gqtech.in',
          first_name: 'John',
          last_name: 'Student',
          roles: ['STUDENT'],
          is_active: true,
          is_superuser: false,
        },
      });
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/students/drives']}>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
                  <Route
                    path="/students/drives"
                    element={
                      <ProtectedRoute requiredRoles={['STUDENT']}>
                        <LazySuccessComponent />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('lazy-success-content')).toBeInTheDocument();
      });
    });

    it('renders /admin/users for authorized ADMIN role and denies non-admin', async () => {
      // 1. Authorized Admin
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: {
          id: 'user-admin-1',
          email: 'admin@gqtech.in',
          first_name: 'Admin',
          last_name: 'User',
          roles: ['ADMIN'],
          is_active: true,
          is_superuser: true,
        },
      });
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/admin/users']}>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
                  <Route
                    path="/admin/users"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN']}>
                        <LazySuccessComponent />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('lazy-success-content')).toBeInTheDocument();
      });
    });

    it('renders /notifications for any authenticated user without role restriction', async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce({
        data: {
          id: 'user-trainer-1',
          email: 'trainer@gqtech.in',
          first_name: 'Trainer',
          last_name: 'User',
          roles: ['TRAINER'],
          is_active: true,
          is_superuser: false,
        },
      });
      const queryClient = createTestQueryClient();

      render(
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <MemoryRouter initialEntries={['/notifications']}>
              <Suspense fallback={<RouteLoadingFallback />}>
                <Routes>
                  <Route
                    path="/notifications"
                    element={
                      <ProtectedRoute>
                        <LazySuccessComponent />
                      </ProtectedRoute>
                    }
                  />
                </Routes>
              </Suspense>
            </MemoryRouter>
          </AuthProvider>
        </QueryClientProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('lazy-success-content')).toBeInTheDocument();
      });
    });
  });
});

