/**
 * Phase 9 Feedback Collection TypeScript Type Definitions
 */

export type DifficultyLevel = 'EASY' | 'MEDIUM' | 'HARD' | 'VERY_HARD';
export type CandidateQuality = 'POOR' | 'FAIR' | 'GOOD' | 'EXCELLENT';
export type StudentReadiness = 'NOT_READY' | 'NEEDS_PRACTICE' | 'READY' | 'HIGHLY_READY';

export interface StudentFeedback {
  id: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  company: string;
  company_name: string;
  job_requirement?: string | null;
  job_title?: string | null;
  interview_schedule?: string | null;
  interview_date?: string | null;
  interview_round?: string | null;
  interview_experience: string;
  technical_questions: string;
  difficulty: DifficultyLevel;
  difficulty_display: string;
  suggestions: string;
  is_anonymous: boolean;
  submitted_by: string;
  submitted_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface StudentFeedbackCreatePayload {
  company: string;
  job_requirement?: string | null;
  interview_schedule?: string | null;
  interview_round?: string | null;
  interview_experience: string;
  technical_questions?: string;
  difficulty: DifficultyLevel;
  suggestions?: string;
  is_anonymous?: boolean;
}

export interface HRFeedback {
  id: string;
  company: string;
  company_name: string;
  hr_contact?: string | null;
  hr_contact_name?: string | null;
  job_requirement?: string | null;
  job_title?: string | null;
  candidate?: string | null;
  candidate_name?: string | null;
  candidate_roll_number?: string | null;
  candidate_quality: CandidateQuality;
  candidate_quality_display: string;
  candidate_quality_remarks: string;
  technical_skills_rating: number;
  technical_skills_remarks: string;
  communication_skills_rating: number;
  communication_skills_remarks: string;
  hiring_satisfaction_rating: number;
  hiring_satisfaction_remarks: string;
  submitted_by: string;
  submitted_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface HRFeedbackCreatePayload {
  company: string;
  hr_contact?: string | null;
  job_requirement?: string | null;
  candidate?: string | null;
  candidate_quality: CandidateQuality;
  candidate_quality_remarks?: string;
  technical_skills_rating: number;
  technical_skills_remarks?: string;
  communication_skills_rating: number;
  communication_skills_remarks?: string;
  hiring_satisfaction_rating: number;
  hiring_satisfaction_remarks?: string;
}

export interface TrainerFeedback {
  id: string;
  student: string;
  student_name: string;
  student_roll_number: string;
  training_session?: string | null;
  session_title?: string | null;
  student_readiness: StudentReadiness;
  student_readiness_display: string;
  student_readiness_remarks: string;
  training_effectiveness_rating: number;
  training_effectiveness_remarks: string;
  areas_for_improvement: string;
  trainer: string;
  trainer_name: string;
  created_at: string;
  updated_at: string;
}

export interface TrainerFeedbackCreatePayload {
  student: string;
  training_session?: string | null;
  student_readiness: StudentReadiness;
  student_readiness_remarks?: string;
  training_effectiveness_rating: number;
  training_effectiveness_remarks?: string;
  areas_for_improvement: string;
}

export interface FeedbackKPIs {
  total_student_feedback: number;
  total_hr_feedback: number;
  total_trainer_feedback: number;
  avg_technical_skills_rating: number;
  avg_communication_skills_rating: number;
  avg_hiring_satisfaction_rating: number;
  avg_training_effectiveness_rating: number;
  difficulty_breakdown: Record<string, number>;
  readiness_breakdown: Record<string, number>;
}

export interface StudentEligibleDrive {
  interview_schedule_id: string;
  company_id: string | null;
  company_name: string;
  job_requirement_id: string | null;
  job_title: string;
  interview_date: string;
}
