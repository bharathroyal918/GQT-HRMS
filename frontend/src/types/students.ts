/**
 * Type definitions for Student Registration, Resumes, Eligibility Engine & Cohorts (Phase 5).
 */

export type JobPublicationChannel = 'WHATSAPP' | 'TELEGRAM' | 'EMAIL' | 'PORTAL';

export type JobPublicationStatus = 'PENDING' | 'QUEUED' | 'DISPATCHED' | 'DELIVERED' | 'FAILED' | 'CANCELLED';

export interface JobPublication {
  id: string;
  job_requirement: string;
  job_title: string;
  company_name: string;
  creative_version: string | null;
  channel: JobPublicationChannel;
  channel_display: string;
  status: JobPublicationStatus;
  status_display: string;
  target_audience: string;
  subject: string;
  message_body: string;
  dispatched_at: string | null;
  delivered_at: string | null;
  failure_reason: string;
  retry_count: number;
  provider_message_id: string;
  published_by: string;
  published_by_name: string;
  created_at: string;
  updated_at: string;
}

export interface JobPublicationCreatePayload {
  job_requirement_id: string;
  channel: JobPublicationChannel;
  target_audience: string;
  creative_version_id?: string | null;
  subject?: string;
  message_body?: string;
}

export interface StudentResume {
  id: string;
  version_number: number;
  file_name: string;
  file_size_bytes: number;
  sha256_hash: string;
  is_current: boolean;
  download_url: string;
  uploaded_at: string;
}

export interface StudentProfile {
  id: string;
  user: string;
  full_name: string;
  email: string;
  roll_number: string;
  institutional_email: string;
  college_name: string;
  degree: string;
  department: string;
  graduation_year: number;
  cgpa: string;
  active_backlogs: number;
  history_backlogs: number;
  phone_number: string;
  alternate_phone: string;
  is_verified_by_placement: boolean;
  current_resume: StudentResume | null;
  resumes: StudentResume[];
  created_at: string;
  updated_at: string;
}

export interface StudentRegisterPayload {
  email: string;
  password: string;
  roll_number: string;
  first_name: string;
  last_name: string;
  college_name: string;
  degree: string;
  department: string;
  graduation_year: number;
  cgpa: string | number;
  active_backlogs?: number;
  history_backlogs?: number;
  phone_number?: string;
  alternate_phone?: string;
}

export interface StudentProfileUpdatePayload {
  college_name?: string;
  degree?: string;
  department?: string;
  graduation_year?: number;
  cgpa?: string | number;
  active_backlogs?: number;
  history_backlogs?: number;
  phone_number?: string;
  alternate_phone?: string;
}

export type EligibilityStatus = 'ELIGIBLE' | 'INELIGIBLE' | 'INCOMPLETE';

export interface EligibilityCriterionDetail {
  criterion: string;
  student_value: string;
  required_value: string;
  passed: boolean;
  details: string;
}

export interface EligibilityEvaluation {
  id: string;
  status: EligibilityStatus;
  status_display: string;
  criteria_snapshot: Record<string, any>;
  evaluation_details: EligibilityCriterionDetail[];
  is_overridden: boolean;
  override_reason: string;
  override_by: string | null;
  override_by_name: string | null;
  override_at: string | null;
  evaluated_at: string;
}

export type StudentApplicationStatus = 'APPLIED' | 'ELIGIBLE' | 'INELIGIBLE' | 'OVERRIDDEN' | 'WITHDRAWN';

export interface StudentApplication {
  id: string;
  student: string;
  student_roll: string;
  student_name: string;
  student_department: string;
  student_cgpa: string;
  student_active_backlogs: number;
  student_graduation_year: number;
  job_requirement: string;
  job_title: string;
  company_name: string;
  resume: string | null;
  resume_id: string | null;
  resume_version: number | null;
  status: StudentApplicationStatus;
  status_display: string;
  applied_at: string;
  eligibility_evaluation?: EligibilityEvaluation;
}

export interface CohortMember {
  id: string;
  student_id: string;
  student_roll: string;
  student_name: string;
  student_email: string;
  student_department: string;
  student_cgpa: string;
  student_active_backlogs: number;
  student_graduation_year: number;
  application: string;
  resume_id: string | null;
  resume_version: number | null;
  is_eligible: boolean;
  is_override: boolean;
  override_reason: string;
  override_by_name: string | null;
  override_at: string | null;
  created_at: string;
}

export interface CandidateCohort {
  id: string;
  job_requirement: string;
  job_title: string;
  company_name: string;
  title: string;
  is_locked: boolean;
  finalized_by: string | null;
  finalized_by_name: string | null;
  finalized_at: string | null;
  finalization_notes: string;
  member_count: number;
  eligible_member_count: number;
  members: CohortMember[];
  created_at: string;
  updated_at: string;
}
