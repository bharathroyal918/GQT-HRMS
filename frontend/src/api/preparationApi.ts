import { apiClient } from '../lib/apiClient';
import {
  ResumeReview,
  ResumeReviewCreatePayload,
  ResumeImprovementCycle,
  AssessmentTest,
  StudentAssessmentAttempt,
  TrainingSession,
  TrainingAttendance,
  RecordAttendancePayload,
  MockInterview,
  ScheduleMockInterviewPayload,
  SubmitMockEvaluationPayload,
  MockInterviewEvaluation,
  PlacementReadinessCertification,
  CertifyPlacementReadinessPayload,
  StudentReadinessSnapshot,
} from '../types/preparation';

export const preparationApi = {
  // Step 15: Resume Review
  async listResumeReviews(params?: { student_id?: string; resume_id?: string; status?: string }): Promise<ResumeReview[]> {
    const res = await apiClient.get<ResumeReview[]>('/preparation/resume-reviews/', { params });
    return res.data;
  },

  async submitResumeReview(data: ResumeReviewCreatePayload): Promise<ResumeReview> {
    const res = await apiClient.post<ResumeReview>('/preparation/resume-reviews/', data);
    return res.data;
  },

  // Step 16: Resume Improvement
  async listImprovementCycles(params?: { student_id?: string }): Promise<ResumeImprovementCycle[]> {
    const res = await apiClient.get<ResumeImprovementCycle[]>('/preparation/improvement-cycles/', { params });
    return res.data;
  },

  async submitImprovedResume(file: File, studentNotes?: string): Promise<{ message: string; resume_id: string; version_number: number; cycle_id: string | null }> {
    const formData = new FormData();
    formData.append('file', file);
    if (studentNotes) {
      formData.append('student_notes', studentNotes);
    }
    const res = await apiClient.post<{ message: string; resume_id: string; version_number: number; cycle_id: string | null }>(
      '/preparation/improvement-cycles/submit/',
      formData,
      {
        headers: { 'Content-Type': 'multipart/form-data' },
      }
    );
    return res.data;
  },

  // Steps 17 & 18: Assessments
  async listAssessmentTests(params?: { test_type?: string }): Promise<AssessmentTest[]> {
    const res = await apiClient.get<AssessmentTest[]>('/preparation/tests/', { params });
    return res.data;
  },

  async getAssessmentTestDetail(testId: string): Promise<AssessmentTest> {
    const res = await apiClient.get<AssessmentTest>(`/preparation/tests/${testId}/`);
    return res.data;
  },

  async startAssessmentAttempt(testId: string): Promise<StudentAssessmentAttempt> {
    const res = await apiClient.post<StudentAssessmentAttempt>('/preparation/attempts/start/', { test_id: testId });
    return res.data;
  },

  async submitAssessmentAttempt(attemptId: string, answers: Record<string, string>): Promise<StudentAssessmentAttempt> {
    const res = await apiClient.post<StudentAssessmentAttempt>('/preparation/attempts/submit/', {
      attempt_id: attemptId,
      answers,
    });
    return res.data;
  },

  async listAssessmentAttempts(params?: { student_id?: string; test_id?: string }): Promise<StudentAssessmentAttempt[]> {
    const res = await apiClient.get<StudentAssessmentAttempt[]>('/preparation/attempts/', { params });
    return res.data;
  },

  // Steps 19 & 20: Training & Corporate Grooming
  async listTrainingSessions(params?: { session_type?: string }): Promise<TrainingSession[]> {
    const res = await apiClient.get<TrainingSession[]>('/preparation/sessions/', { params });
    return res.data;
  },

  async createTrainingSession(data: {
    title: string;
    session_type: string;
    scheduled_at: string;
    venue_or_link: string;
    description?: string;
  }): Promise<TrainingSession> {
    const res = await apiClient.post<TrainingSession>('/preparation/sessions/', data);
    return res.data;
  },

  async listTrainingAttendances(params?: { session_id?: string; student_id?: string }): Promise<TrainingAttendance[]> {
    const res = await apiClient.get<TrainingAttendance[]>('/preparation/attendances/', { params });
    return res.data;
  },

  async recordTrainingAttendance(data: RecordAttendancePayload): Promise<TrainingAttendance> {
    const res = await apiClient.post<TrainingAttendance>('/preparation/attendances/record/', data);
    return res.data;
  },

  // Steps 21 & 22: Mock Interviews & Evaluations
  async listMockInterviews(params?: { student_id?: string; evaluator_id?: string; status?: string }): Promise<MockInterview[]> {
    const res = await apiClient.get<MockInterview[]>('/preparation/mock-interviews/', { params });
    return res.data;
  },

  async scheduleMockInterview(data: ScheduleMockInterviewPayload): Promise<MockInterview> {
    const res = await apiClient.post<MockInterview>('/preparation/mock-interviews/', data);
    return res.data;
  },

  async submitMockEvaluation(data: SubmitMockEvaluationPayload): Promise<MockInterviewEvaluation> {
    const res = await apiClient.post<MockInterviewEvaluation>('/preparation/mock-interviews/evaluate/', data);
    return res.data;
  },

  // Step 23: Placement Readiness Certification Gate
  async getStudentReadinessSnapshot(studentId: string): Promise<StudentReadinessSnapshot> {
    const res = await apiClient.get<StudentReadinessSnapshot>(`/preparation/readiness-snapshot/${studentId}/`);
    return res.data;
  },

  async listPlacementCertifications(params?: { student_id?: string; is_approved?: boolean }): Promise<PlacementReadinessCertification[]> {
    const res = await apiClient.get<PlacementReadinessCertification[]>('/preparation/certifications/', { params });
    return res.data;
  },

  async certifyPlacementReadiness(data: CertifyPlacementReadinessPayload): Promise<PlacementReadinessCertification> {
    const res = await apiClient.post<PlacementReadinessCertification>('/preparation/certifications/certify/', data);
    return res.data;
  },
};
