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
import { CrmReconciliationPage } from './pages/crm/CrmReconciliationPage';
import { JobDirectoryPage } from './pages/jobs/JobDirectoryPage';
import { JobFormPage } from './pages/jobs/JobFormPage';
import { JobDetailPage } from './pages/jobs/JobDetailPage';
import { JobApprovalsQueuePage } from './pages/jobs/JobApprovalsQueuePage';
import { CreativeDirectoryPage } from './pages/creatives/CreativeDirectoryPage';
import { CreativeRequestFormPage } from './pages/creatives/CreativeRequestFormPage';
import { CreativeDetailPage } from './pages/creatives/CreativeDetailPage';
import { CreativeReviewQueuePage } from './pages/creatives/CreativeReviewQueuePage';
import { DesignerWorkQueuePage } from './pages/creatives/DesignerWorkQueuePage';
import { JobPublicationPage } from './pages/students/JobPublicationPage';
import { StudentRegistrationPage } from './pages/students/StudentRegistrationPage';
import { StudentProfileWorkspacePage } from './pages/students/StudentProfileWorkspacePage';
import { EligibilityWorkspacePage } from './pages/students/EligibilityWorkspacePage';
import { CandidateCohortPage } from './pages/students/CandidateCohortPage';
import { StudentDirectoryPage } from './pages/students/StudentDirectoryPage';
import { ResumeReviewWorkspacePage } from './pages/preparation/ResumeReviewWorkspacePage';
import { StudentAssessmentsPage } from './pages/preparation/StudentAssessmentsPage';
import { MockInterviewWorkspacePage } from './pages/preparation/MockInterviewWorkspacePage';
import { PlacementReadinessGatePage } from './pages/preparation/PlacementReadinessGatePage';
import { CandidateSubmissionWorkspacePage } from './pages/submissions/CandidateSubmissionWorkspacePage';
import { InterviewWorkspacePage } from './pages/interviews/InterviewWorkspacePage';
import { PlacementWorkspacePage } from './pages/placements/PlacementWorkspacePage';
import { FeedbackWorkspacePage } from './pages/feedback/FeedbackWorkspacePage';
import { ReportsHubPage } from './pages/reports/ReportsHubPage';
import { ContinuousImprovementHubPage } from './pages/improvement/ContinuousImprovementHubPage';

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
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
};

export default App;
