import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';
import { DiagnosticsPage } from './pages/DiagnosticsPage';
import { NotFoundPage } from './pages/NotFoundPage';
import { LoginPage } from './pages/auth/LoginPage';
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage';
import { AccessDeniedPage } from './pages/auth/AccessDeniedPage';
import { CrmDashboardPage } from './pages/crm/CrmDashboardPage';
import { CompaniesPage } from './pages/crm/CompaniesPage';
import { CompanyFormPage } from './pages/crm/CompanyFormPage';
import { CompanyDetailPage } from './pages/crm/CompanyDetailPage';
import { ContactsPage } from './pages/crm/ContactsPage';
import { ContactFormPage } from './pages/crm/ContactFormPage';
import { OutreachPage } from './pages/crm/OutreachPage';
import { OutreachFormPage } from './pages/crm/OutreachFormPage';
import { FollowUpsPage } from './pages/crm/FollowUpsPage';

const CRM_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'AUDITOR'];

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
            <Route path="/access-denied" element={<AccessDeniedPage />} />

            {/* Authenticated Workspace Application */}
            <Route element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route
                path="diagnostics"
                element={
                  <ProtectedRoute requiredRoles={['ADMIN']}>
                    <DiagnosticsPage />
                  </ProtectedRoute>
                }
              />

              {/* Corporate CRM & HR Directory */}
              <Route
                path="crm"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <CrmDashboardPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/companies"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <CompaniesPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/companies/new"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <CompanyFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/companies/:id"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <CompanyDetailPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/companies/:id/edit"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <CompanyFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/contacts"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <ContactsPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/contacts/new"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <ContactFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/outreach"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <OutreachPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/outreach/new"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <OutreachFormPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="crm/follow-ups"
                element={
                  <ProtectedRoute requiredRoles={CRM_ROLES}>
                    <FollowUpsPage />
                  </ProtectedRoute>
                }
              />

              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
