import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppShell } from './components/layout/AppShell';
import { RouteLoadingFallback } from './components/layout/RouteLoadingFallback';
import { RouteErrorBoundary } from './components/common/RouteErrorBoundary';

// Public & Auth Routes (Lazy Loaded)
const LoginPage = lazy(() => import('./pages/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const ForgotPasswordPage = lazy(() => import('./pages/auth/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('./pages/auth/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })));
const AccessDeniedPage = lazy(() => import('./pages/auth/AccessDeniedPage').then(m => ({ default: m.AccessDeniedPage })));
const StudentRegistrationPage = lazy(() => import('./pages/students/StudentRegistrationPage').then(m => ({ default: m.StudentRegistrationPage })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

// Core Workspaces (Lazy Loaded)
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const DiagnosticsPage = lazy(() => import('./pages/DiagnosticsPage').then(m => ({ default: m.DiagnosticsPage })));
const UserManagementPage = lazy(() => import('./pages/admin/UserManagementPage').then(m => ({ default: m.UserManagementPage })));
const NotificationsPage = lazy(() => import('./pages/notifications/NotificationsPage').then(m => ({ default: m.NotificationsPage })));

// CRM Workspace (Lazy Loaded)
const CrmDashboardPage = lazy(() => import('./pages/crm/CrmDashboardPage').then(m => ({ default: m.CrmDashboardPage })));
const CompaniesPage = lazy(() => import('./pages/crm/CompaniesPage').then(m => ({ default: m.CompaniesPage })));
const CompanyFormPage = lazy(() => import('./pages/crm/CompanyFormPage').then(m => ({ default: m.CompanyFormPage })));
const CompanyDetailPage = lazy(() => import('./pages/crm/CompanyDetailPage').then(m => ({ default: m.CompanyDetailPage })));
const ContactsPage = lazy(() => import('./pages/crm/ContactsPage').then(m => ({ default: m.ContactsPage })));
const ContactFormPage = lazy(() => import('./pages/crm/ContactFormPage').then(m => ({ default: m.ContactFormPage })));
const OutreachPage = lazy(() => import('./pages/crm/OutreachPage').then(m => ({ default: m.OutreachPage })));
const OutreachFormPage = lazy(() => import('./pages/crm/OutreachFormPage').then(m => ({ default: m.OutreachFormPage })));
const FollowUpsPage = lazy(() => import('./pages/crm/FollowUpsPage').then(m => ({ default: m.FollowUpsPage })));
const CrmReconciliationPage = lazy(() => import('./pages/crm/CrmReconciliationPage').then(m => ({ default: m.CrmReconciliationPage })));

// Job Requirements Workspace (Lazy Loaded)
const JobDirectoryPage = lazy(() => import('./pages/jobs/JobDirectoryPage').then(m => ({ default: m.JobDirectoryPage })));
const JobFormPage = lazy(() => import('./pages/jobs/JobFormPage').then(m => ({ default: m.JobFormPage })));
const JobDetailPage = lazy(() => import('./pages/jobs/JobDetailPage').then(m => ({ default: m.JobDetailPage })));
const JobApprovalsQueuePage = lazy(() => import('./pages/jobs/JobApprovalsQueuePage').then(m => ({ default: m.JobApprovalsQueuePage })));

// Creative Studio Workspace (Lazy Loaded)
const CreativeDirectoryPage = lazy(() => import('./pages/creatives/CreativeDirectoryPage').then(m => ({ default: m.CreativeDirectoryPage })));
const CreativeRequestFormPage = lazy(() => import('./pages/creatives/CreativeRequestFormPage').then(m => ({ default: m.CreativeRequestFormPage })));
const CreativeDetailPage = lazy(() => import('./pages/creatives/CreativeDetailPage').then(m => ({ default: m.CreativeDetailPage })));
const CreativeReviewQueuePage = lazy(() => import('./pages/creatives/CreativeReviewQueuePage').then(m => ({ default: m.CreativeReviewQueuePage })));
const DesignerWorkQueuePage = lazy(() => import('./pages/creatives/DesignerWorkQueuePage').then(m => ({ default: m.DesignerWorkQueuePage })));

// Student Registration & Eligibility Engine (Lazy Loaded)
const JobPublicationPage = lazy(() => import('./pages/students/JobPublicationPage').then(m => ({ default: m.JobPublicationPage })));
const StudentProfileWorkspacePage = lazy(() => import('./pages/students/StudentProfileWorkspacePage').then(m => ({ default: m.StudentProfileWorkspacePage })));
const EligibilityWorkspacePage = lazy(() => import('./pages/students/EligibilityWorkspacePage').then(m => ({ default: m.EligibilityWorkspacePage })));
const CandidateCohortPage = lazy(() => import('./pages/students/CandidateCohortPage').then(m => ({ default: m.CandidateCohortPage })));
const StudentDirectoryPage = lazy(() => import('./pages/students/StudentDirectoryPage').then(m => ({ default: m.StudentDirectoryPage })));
const StudentDrivesPage = lazy(() => import('./pages/students/StudentDrivesPage').then(m => ({ default: m.StudentDrivesPage })));

// Student Preparation (Lazy Loaded)
const ResumeReviewWorkspacePage = lazy(() => import('./pages/preparation/ResumeReviewWorkspacePage').then(m => ({ default: m.ResumeReviewWorkspacePage })));
const StudentAssessmentsPage = lazy(() => import('./pages/preparation/StudentAssessmentsPage').then(m => ({ default: m.StudentAssessmentsPage })));
const MockInterviewWorkspacePage = lazy(() => import('./pages/preparation/MockInterviewWorkspacePage').then(m => ({ default: m.MockInterviewWorkspacePage })));
const PlacementReadinessGatePage = lazy(() => import('./pages/preparation/PlacementReadinessGatePage').then(m => ({ default: m.PlacementReadinessGatePage })));

// Candidate Submissions & Placement Operations (Lazy Loaded)
const CandidateSubmissionWorkspacePage = lazy(() => import('./pages/submissions/CandidateSubmissionWorkspacePage').then(m => ({ default: m.CandidateSubmissionWorkspacePage })));
const InterviewWorkspacePage = lazy(() => import('./pages/interviews/InterviewWorkspacePage').then(m => ({ default: m.InterviewWorkspacePage })));
const PlacementWorkspacePage = lazy(() => import('./pages/placements/PlacementWorkspacePage').then(m => ({ default: m.PlacementWorkspacePage })));
const FeedbackWorkspacePage = lazy(() => import('./pages/feedback/FeedbackWorkspacePage').then(m => ({ default: m.FeedbackWorkspacePage })));
const ReportsHubPage = lazy(() => import('./pages/reports/ReportsHubPage').then(m => ({ default: m.ReportsHubPage })));
const ContinuousImprovementHubPage = lazy(() => import('./pages/improvement/ContinuousImprovementHubPage').then(m => ({ default: m.ContinuousImprovementHubPage })));

const CRM_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'AUDITOR'];
const JOB_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'CREATIVE_DESIGNER', 'AUDITOR'];
const CREATIVE_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'CREATIVE_DESIGNER', 'AUDITOR'];
const STAFF_PUBLISH_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'];
const COHORT_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR'];
const PREPARATION_GATE_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR'];
const SUBMISSION_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'AUDITOR'];
const INTERVIEW_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'EVALUATOR', 'TRAINER', 'STUDENT', 'AUDITOR'];
const PLACEMENT_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'STUDENT', 'AUDITOR'];
const FEEDBACK_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'TRAINER', 'EVALUATOR', 'STUDENT', 'AUDITOR'];
const REPORT_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'AUDITOR', 'STUDENT'];
const IMPROVEMENT_ROLES = ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR', 'TRAINER', 'EVALUATOR', 'AUDITOR'];

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <RouteErrorBoundary>
            <Suspense fallback={<RouteLoadingFallback fullScreen />}>
              <Routes>
                {/* Public Authentication Routes */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
                <Route path="/access-denied" element={<AccessDeniedPage />} />
                <Route path="/students/register" element={<StudentRegistrationPage />} />

                {/* Authenticated Workspace Application */}
                <Route element={<AppShell />}>
                  <Route index element={<DashboardPage />} />
                  <Route
                    path="notifications"
                    element={
                      <ProtectedRoute>
                        <NotificationsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="diagnostics"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN']}>
                        <DiagnosticsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="admin/users"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN']}>
                        <UserManagementPage />
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
                  <Route
                    path="crm/reconciliation"
                    element={
                      <ProtectedRoute requiredRoles={CRM_ROLES}>
                        <CrmReconciliationPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Job Requirements & Verification Checklist (Phase 3) */}
                  <Route
                    path="jobs"
                    element={
                      <ProtectedRoute requiredRoles={JOB_ROLES}>
                        <JobDirectoryPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/new"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']}>
                        <JobFormPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/:id"
                    element={
                      <ProtectedRoute requiredRoles={JOB_ROLES}>
                        <JobDetailPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/:id/edit"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']}>
                        <JobFormPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/approvals"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR']}>
                        <JobApprovalsQueuePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Creative Studio & Promotional Assets Management (Phase 4 / Steps 8-9) */}
                  <Route
                    path="creatives"
                    element={
                      <ProtectedRoute requiredRoles={CREATIVE_ROLES}>
                        <CreativeDirectoryPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="creatives/new"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']}>
                        <CreativeRequestFormPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="creatives/queue"
                    element={
                      <ProtectedRoute requiredRoles={['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'AUDITOR']}>
                        <CreativeReviewQueuePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="creatives/my-tasks"
                    element={
                      <ProtectedRoute requiredRoles={['CREATIVE_DESIGNER', 'ADMIN']}>
                        <DesignerWorkQueuePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="creatives/:id"
                    element={
                      <ProtectedRoute requiredRoles={CREATIVE_ROLES}>
                        <CreativeDetailPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Student Registration & Eligibility Engine (Phase 5 / Steps 10-14) */}
                  <Route
                    path="students/profile"
                    element={<StudentProfileWorkspacePage />}
                  />
                  <Route
                    path="students/drives"
                    element={
                      <ProtectedRoute requiredRoles={['STUDENT']}>
                        <StudentDrivesPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="students"
                    element={
                      <ProtectedRoute requiredRoles={COHORT_ROLES}>
                        <StudentDirectoryPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/:id/publish"
                    element={
                      <ProtectedRoute requiredRoles={STAFF_PUBLISH_ROLES}>
                        <JobPublicationPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/:id/eligibility"
                    element={
                      <ProtectedRoute requiredRoles={JOB_ROLES}>
                        <EligibilityWorkspacePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="jobs/:id/cohort"
                    element={
                      <ProtectedRoute requiredRoles={COHORT_ROLES}>
                        <CandidateCohortPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Student Preparation (Phase 6 / Steps 15-23) */}
                  <Route
                    path="preparation/resume-reviews"
                    element={<ResumeReviewWorkspacePage />}
                  />
                  <Route
                    path="preparation/assessments"
                    element={<StudentAssessmentsPage />}
                  />
                  <Route
                    path="preparation/mock-interviews"
                    element={<MockInterviewWorkspacePage />}
                  />
                  <Route
                    path="preparation/readiness-gate"
                    element={
                      <ProtectedRoute requiredRoles={PREPARATION_GATE_ROLES}>
                        <PlacementReadinessGatePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Candidate Submissions & Profile Dispatch (Phase 7 / Steps 24-28) */}
                  <Route
                    path="submissions"
                    element={
                      <ProtectedRoute requiredRoles={SUBMISSION_ROLES}>
                        <CandidateSubmissionWorkspacePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Interview Management & Tracking (Phase 8 / Steps 29-35) */}
                  <Route
                    path="interviews"
                    element={
                      <ProtectedRoute requiredRoles={INTERVIEW_ROLES}>
                        <InterviewWorkspacePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Placement Management & Tracking (Phase 8 / Steps 36-41) */}
                  <Route
                    path="placements"
                    element={
                      <ProtectedRoute requiredRoles={PLACEMENT_ROLES}>
                        <PlacementWorkspacePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Feedback Collection (Phase 9 / Categories A, B, C) */}
                  <Route
                    path="feedback"
                    element={
                      <ProtectedRoute requiredRoles={FEEDBACK_ROLES}>
                        <FeedbackWorkspacePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Reports & Analytics (Phase 11 / Steps 48-52) */}
                  <Route
                    path="reports"
                    element={
                      <ProtectedRoute requiredRoles={REPORT_ROLES}>
                        <ReportsHubPage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Continuous Improvement & Strategic Planning (Phase 13) */}
                  <Route
                    path="continuous-improvement"
                    element={
                      <ProtectedRoute requiredRoles={IMPROVEMENT_ROLES}>
                        <ContinuousImprovementHubPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="improvement"
                    element={
                      <ProtectedRoute requiredRoles={IMPROVEMENT_ROLES}>
                        <ContinuousImprovementHubPage />
                      </ProtectedRoute>
                    }
                  />

                  <Route path="*" element={<NotFoundPage />} />
                </Route>
              </Routes>
            </Suspense>
          </RouteErrorBoundary>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
