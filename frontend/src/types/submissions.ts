/**
 * TypeScript Type Definitions for Candidate Submissions & Profile Dispatch (Phase 7 / Steps 24-28).
 */

export interface CandidateReadinessItem {
  student_id: string;
  student_name: string;
  roll_number: string;
  institutional_email: string;
  phone_number: string;
  college_name: string;
  department: string;
  graduation_year: number;
  cgpa: number | null;
  technical_skills: string;
  application_id: string;
  application_status: string;
  is_in_locked_cohort: boolean;
  has_readiness_certification: boolean;
  certification_id: string | null;
  approved_resume_id: string | null;
  approved_resume_version: number | null;
  approved_resume_file_name: string | null;
  approved_resume_sha256: string | null;
  is_already_submitted: boolean;
  can_be_submitted: boolean;
}

export interface JobEligibleCandidatesResponse {
  job_id: string;
  job_title: string;
  company_name: string;
  hr_contact_name: string;
  hr_contact_email: string;
  total_eligible: number;
  total_certified: number;
  candidates: CandidateReadinessItem[];
}

export interface CandidateSubmission {
  id: string;
  student_id: string;
  roll_number: string;
  student_name: string;
  institutional_email: string;
  phone_number: string;
  department: string;
  graduation_year: number;
  cgpa: string | number | null;
  resume_id: string;
  resume_version_number: number;
  resume_sha256: string;
  resume_file_url: string;
  status: 'PENDING' | 'SUBMITTED' | 'ACKNOWLEDGED' | 'SHORTLISTED' | 'REJECTED' | 'ON_HOLD';
  candidate_snapshot: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SubmissionDispatchLog {
  id: string;
  attempt_number: number;
  channel: 'EMAIL' | 'WHATSAPP' | 'PORTAL_LINK' | 'DIRECT_HANDOFF';
  recipient: string;
  status: 'QUEUED' | 'SENT' | 'DELIVERED' | 'FAILED';
  provider_message_id: string;
  response_payload: Record<string, any>;
  dispatched_by_name: string;
  timestamp: string;
}

export interface SubmissionPackageListItem {
  id: string;
  title: string;
  job_id: string;
  job_title: string;
  company_id: string;
  company_name: string;
  hr_contact_id: string;
  hr_contact_name: string;
  status: 'DRAFT' | 'READY_FOR_DISPATCH' | 'DISPATCHED' | 'ACKNOWLEDGED' | 'CANCELLED';
  candidate_count: number;
  package_hash: string;
  roster_file_name: string;
  has_roster_file: boolean;
  created_at: string;
  dispatched_at: string | null;
  acknowledged_at: string | null;
  created_by_name: string;
  dispatched_by_name: string | null;
}

export interface SubmissionPackage extends SubmissionPackageListItem {
  hr_contact_email: string;
  hr_contact_phone: string;
  roster_download_url: string;
  roster_generated_at: string | null;
  resumes_attached_at: string | null;
  notes: string;
  dispatch_channel: 'EMAIL' | 'WHATSAPP' | 'PORTAL_LINK' | 'DIRECT_HANDOFF';
  recipient_email: string;
  recipient_name: string;
  recipient_phone: string;
  provider_reference: string;
  dispatch_notes: string;
  acknowledged_by_name: string | null;
  acknowledged_by_contact_name: string;
  acknowledgement_channel: 'EMAIL' | 'PHONE_CALL' | 'WHATSAPP' | 'PORTAL' | 'IN_PERSON';
  recruiter_feedback: string;
  tentative_interview_date: string | null;
  follow_up_callback_date: string | null;
  candidates: CandidateSubmission[];
  dispatch_logs: SubmissionDispatchLog[];
}

export interface CreateSubmissionPackagePayload {
  job_requirement_id: string;
  candidate_student_ids: string[];
  title?: string;
  notes?: string;
}

export interface DispatchPackagePayload {
  channel: 'EMAIL' | 'WHATSAPP' | 'PORTAL_LINK' | 'DIRECT_HANDOFF';
  recipient_email?: string;
  recipient_name?: string;
  recipient_phone?: string;
  dispatch_notes?: string;
}

export interface RecordAcknowledgementPayload {
  acknowledged_by_contact_name: string;
  acknowledgement_channel?: 'EMAIL' | 'PHONE_CALL' | 'WHATSAPP' | 'PORTAL' | 'IN_PERSON';
  recruiter_feedback?: string;
  tentative_interview_date?: string | null;
  follow_up_callback_date?: string | null;
}

export interface StudentSubmission {
  id: string;
  package_id: string;
  job_title: string;
  company_name: string;
  status: string;
  resume_version: number;
  dispatched_at: string | null;
  created_at: string;
}
