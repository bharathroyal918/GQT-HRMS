/**
 * Job Requirement & 5-Point Verification Checklist Type Definitions (Phase 3).
 *
 * Preserves the authoritative GQT HRMS workflow:
 * - Step 5: Collect Job Description
 * - Step 6: Verify Job Details (5 Core Points)
 * - Step 7: Internal Approval
 */

export type JobRequirementStatus =
  | 'DRAFT'
  | 'PENDING_VERIFICATION'
  | 'UNDER_REVIEW'
  | 'CHANGES_REQUESTED'
  | 'VERIFIED'
  | 'APPROVED'
  | 'REJECTED';

export type EmploymentType =
  | 'FULL_TIME'
  | 'INTERNSHIP'
  | 'INTERNSHIP_PPO'
  | 'CONTRACT';

export type WorkArrangement = 'ON_SITE' | 'HYBRID' | 'REMOTE';

export type ChecklistItemStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'REJECTED'
  | 'NOT_APPLICABLE';

export type ChecklistItemCode =
  | 'ELIGIBILITY'
  | 'SALARY_AUTHENTICITY'
  | 'COMPANY_AUTHENTICITY'
  | 'INTERVIEW_PROCESS'
  | 'REGISTRATION_DEADLINE';

export interface JobChecklistItem {
  id: string;
  item_code: ChecklistItemCode;
  title: string;
  description: string;
  is_mandatory: boolean;
  status: ChecklistItemStatus;
  verified_by: string | null;
  verified_by_name: string;
  verified_at: string | null;
  remarks: string;
}

export interface JobApprovalDecision {
  id: string;
  decision: string;
  actor: string | null;
  actor_name: string;
  actor_role: string;
  comments: string;
  created_at: string;
}

export interface JobChecklistProgress {
  total_mandatory: number;
  verified_mandatory: number;
  percentage: number;
  is_complete: boolean;
}

export interface JobRequirementListItem {
  id: string;
  title: string;
  company: string;
  company_name: string;
  company_tier: string;
  hr_contact: string | null;
  hr_contact_name: string;
  location: string;
  work_arrangement: WorkArrangement;
  employment_type: EmploymentType;
  min_salary: string | null;
  max_salary: string | null;
  salary_currency: string;
  status: JobRequirementStatus;
  registration_deadline: string;
  openings_count: number;
  checklist_progress: JobChecklistProgress;
  is_archived: boolean;
  created_at: string;
}

export interface JobRequirementDetail {
  id: string;
  company: string;
  company_name: string;
  company_website: string;
  company_domain: string;
  company_tier: string;
  company_category: string;
  hr_contact: string | null;
  hr_contact_name: string;
  hr_contact_email: string;
  hr_contact_phone: string;
  title: string;
  job_description: string;
  skills_required: string;
  min_salary: string | null;
  max_salary: string | null;
  salary_currency: string;
  salary_breakup: string;
  location: string;
  work_arrangement: WorkArrangement;
  employment_type: EmploymentType;
  has_bond: boolean;
  bond_details: string;
  eligibility_criteria: string;
  min_cgpa: string | null;
  hiring_process: string;
  interview_date: string | null;
  registration_deadline: string;
  openings_count: number;
  status: JobRequirementStatus;
  created_by: string | null;
  created_by_name: string;
  assigned_verifier: string | null;
  assigned_verifier_name: string;
  verified_by: string | null;
  verified_by_name: string;
  verified_at: string | null;
  approved_by: string | null;
  approved_by_name: string;
  approved_at: string | null;
  rejection_reason: string;
  return_reason: string;
  notes: string;
  is_archived: boolean;
  checklist_items: JobChecklistItem[];
  decisions: JobApprovalDecision[];
  checklist_progress: JobChecklistProgress;
  is_locked: boolean;
  is_editable: boolean;
  created_at: string;
  updated_at: string;
}

export interface JobMetrics {
  total_active: number;
  draft_count: number;
  pending_verification_count: number;
  under_review_count: number;
  changes_requested_count: number;
  verified_count: number;
  approved_count: number;
  rejected_count: number;
  deadlines_approaching_count: number;
}
