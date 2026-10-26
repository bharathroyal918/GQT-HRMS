/**
 * Type definitions for Student Preparation Domain (Phase 6 / Workflow Steps 15-23).
 */

export type ResumeReviewStatus = 'PENDING' | 'APPROVED' | 'REVISION_REQUESTED';

export interface ResumeReview {
  id: string;
  resume: string;
  resume_version: number;
  student: string;
  student_name: string;
  student_roll_number: string;
  reviewer: string;
  reviewer_name: string;
  status: ResumeReviewStatus;
  formatting_score: number;
  technical_skills_score: number;
  projects_score: number;
  achievements_score: number;
  aggregate_score: number;
  detailed_feedback: string;
  suggested_improvements: string;
  reviewed_at: string;
  created_at: string;
  updated_at: string;
}

export interface ResumeReviewCreatePayload {
  resume_id: string;
  status: 'APPROVED' | 'REVISION_REQUESTED';
  formatting_score: number;
  technical_skills_score: number;
  projects_score: number;
  achievements_score: number;
  detailed_feedback: string;
  suggested_improvements?: string;
}

export type ImprovementCycleStatus = 'REVISION_PENDING' | 'REVISED_UPLOADED' | 'RE_REVIEWED';

export interface ResumeImprovementCycle {
  id: string;
  initial_review: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  prior_resume: string;
  prior_resume_version: number;
  improved_resume: string | null;
  improved_resume_version: number | null;
  status: ImprovementCycleStatus;
  student_notes: string;
  submitted_at: string | null;
  created_at: string;
  updated_at: string;
}

export type AssessmentTestType = 'APTITUDE' | 'TECHNICAL';

export interface QuestionOption {
  id: string;
  text: string;
}

export interface AssessmentQuestion {
  id: number | string;
  question_text: string;
  options: QuestionOption[];
  marks: number;
  correct_option_id?: string;
  explanation?: string;
}

export interface AssessmentTest {
  id: string;
  title: string;
  test_type: AssessmentTestType;
  domain_track: string;
  description: string;
  duration_minutes: number;
  total_marks: number;
  passing_marks: number;
  question_count?: number;
  questions?: AssessmentQuestion[];
  is_active: boolean;
  created_by_name: string;
  created_at: string;
}

export type AssessmentAttemptStatus = 'IN_PROGRESS' | 'COMPLETED' | 'EXPIRED';

export interface StudentAssessmentAttempt {
  id: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  test: string;
  test_title: string;
  test_type: AssessmentTestType;
  attempt_number: number;
  score: number;
  total_marks: number;
  passing_marks: number;
  percentage: string;
  passed: boolean;
  status: AssessmentAttemptStatus;
  answers: Record<string, string>;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

export type TrainingSessionType = 'COMMUNICATION' | 'CORPORATE_GROOMING';

export interface TrainingSession {
  id: string;
  title: string;
  session_type: TrainingSessionType;
  trainer: string;
  trainer_name: string;
  scheduled_at: string;
  venue_or_link: string;
  description: string;
  is_completed: boolean;
  attendee_count: number;
  created_at: string;
}

export type AttendanceStatus = 'ATTENDED' | 'ABSENT' | 'EXCUSED';

export interface TrainingAttendance {
  id: string;
  session: string;
  session_title: string;
  session_type: TrainingSessionType;
  student: string;
  student_name: string;
  student_roll_number: string;
  attendance_status: AttendanceStatus;
  presentation_score: number | null;
  professional_etiquette_verified: boolean;
  corporate_communication_verified: boolean;
  dress_code_verified: boolean;
  hr_interview_ready: boolean;
  grooming_certified: boolean;
  trainer_remarks: string;
  created_at: string;
  updated_at: string;
}

export interface RecordAttendancePayload {
  session_id: string;
  student_id: string;
  attendance_status: AttendanceStatus;
  presentation_score?: number | null;
  professional_etiquette_verified?: boolean;
  corporate_communication_verified?: boolean;
  dress_code_verified?: boolean;
  hr_interview_ready?: boolean;
  grooming_certified?: boolean;
  trainer_remarks?: string;
}

export type MockInterviewType = 'TECHNICAL' | 'HR' | 'COMBINED';
export type MockInterviewStatus = 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW';
export type MockReadinessRecommendation = 'READY_FOR_PLACEMENTS' | 'NEEDS_PRACTICE' | 'NOT_READY';

export interface MockInterviewEvaluation {
  id: string;
  mock_interview: string;
  evaluator: string;
  evaluator_name: string;
  technical_competence_score: number;
  problem_solving_score: number;
  communication_clarity_score: number;
  professional_readiness_score: number;
  total_score: number;
  technical_feedback: string;
  communication_feedback: string;
  improvement_suggestions: string;
  readiness_recommendation: MockReadinessRecommendation;
  evaluated_at: string;
}

export interface MockInterview {
  id: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  evaluator: string;
  evaluator_name: string;
  scheduled_by: string;
  scheduled_by_name: string;
  interview_type: MockInterviewType;
  scheduled_at: string;
  meeting_link: string;
  status: MockInterviewStatus;
  notes: string;
  evaluation?: MockInterviewEvaluation | null;
  created_at: string;
}

export interface ScheduleMockInterviewPayload {
  student_id: string;
  evaluator_id: string;
  scheduled_at: string;
  interview_type: MockInterviewType;
  meeting_link?: string;
  notes?: string;
}

export interface SubmitMockEvaluationPayload {
  mock_interview_id: string;
  technical_competence_score: number;
  problem_solving_score: number;
  communication_clarity_score: number;
  professional_readiness_score: number;
  technical_feedback: string;
  communication_feedback: string;
  improvement_suggestions: string;
  readiness_recommendation: MockReadinessRecommendation;
}

export type PlacementReadinessStatus = 'CERTIFIED' | 'REJECTED';

export interface PlacementReadinessCertification {
  id: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  department: string;
  approved_resume: string;
  approved_resume_version: number;
  is_approved_for_placements: boolean;
  status: PlacementReadinessStatus;
  certified_by: string;
  certified_by_name: string;
  certified_at: string;
  readiness_summary: Record<string, any>;
  notes: string;
  created_at: string;
}

export interface CertifyPlacementReadinessPayload {
  student_id: string;
  approved_resume_id: string;
  is_approved: boolean;
  notes?: string;
}

export interface StudentReadinessSnapshot {
  student_id: string;
  student_name: string;
  roll_number: string;
  department: string;
  current_resume_id: string | null;
  current_resume_version: number | null;
  criteria: {
    resume_review_approved: boolean;
    resume_review_id: string | null;
    aptitude_assessment_passed: boolean;
    aptitude_score: number | null;
    technical_assessment_passed: boolean;
    technical_score: number | null;
    communication_attended: boolean;
    grooming_certified: boolean;
    mock_interview_completed: boolean;
    mock_interview_ready: boolean;
    mock_total_score: number | null;
  };
  all_criteria_met: boolean;
  is_placement_certified: boolean;
  current_certification?: {
    is_approved_for_placements: boolean;
    status: PlacementReadinessStatus;
    certified_by: string;
    certified_at: string;
    notes: string;
  } | null;
}
