/**
 * Creative Studio & Promotional Assets Type Definitions (Phase 4).
 *
 * Preserves the authoritative GQT HRMS workflow:
 * - Step 8: Send to Design Team (Flyer, Banner, Social Media Post)
 * - Step 9: Review & Approve Design (4-Point Checklist: Flyer accuracy, Logo, QR code, Registration link & contacts)
 */

export type CreativeDeliverableType =
  | 'FLYER'
  | 'BANNER'
  | 'SOCIAL_POST'
  | 'COMBINED_PACK';

export type CreativeRequestStatus =
  | 'DRAFT'
  | 'ASSIGNED'
  | 'IN_PRODUCTION'
  | 'REVIEW_PENDING'
  | 'CHANGES_REQUESTED'
  | 'APPROVED'
  | 'REJECTED'
  | 'CANCELLED';

export type CreativePriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type AssetVersionStatus =
  | 'DRAFT'
  | 'SUBMITTED'
  | 'IN_REVIEW'
  | 'CHANGES_REQUESTED'
  | 'APPROVED'
  | 'REJECTED';

export type ChecklistItemCode =
  | 'FLYER_ACCURACY'
  | 'OFFICIAL_LOGO'
  | 'QR_CODE'
  | 'REGISTRATION_LINK_AND_CONTACTS';

export type ChecklistItemStatus =
  | 'PENDING'
  | 'VERIFIED'
  | 'REJECTED'
  | 'NOT_APPLICABLE';

export interface UserMinimal {
  id: string;
  email: string;
  full_name: string;
}

export interface CreativeChecklistItem {
  id: string;
  item_code: ChecklistItemCode;
  item_code_display: string;
  title: string;
  description: string;
  is_mandatory: boolean;
  status: ChecklistItemStatus;
  verified_by: UserMinimal | null;
  verified_at: string | null;
  remarks: string;
  created_at: string;
  updated_at: string;
}

export interface CreativeDecision {
  id: string;
  decision: string;
  actor: UserMinimal | null;
  actor_role: string;
  comments: string;
  snapshot_version_number: number | null;
  snapshot_request_status: string;
  created_at: string;
}

export interface ChecklistProgress {
  total: number;
  verified: number;
  percent: number;
  all_verified: boolean;
}

export interface CreativeAssetVersion {
  id: string;
  version_number: number;
  deliverable_type: CreativeDeliverableType;
  deliverable_type_display: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  sha256_hash: string;
  width_px: number | null;
  height_px: number | null;
  designer_notes: string;
  status: AssetVersionStatus;
  status_display: string;
  uploaded_by: UserMinimal;
  is_approved: boolean;
  approved_by: UserMinimal | null;
  approved_at: string | null;
  rejection_reason: string;
  checklist_items: CreativeChecklistItem[];
  checklist_progress: ChecklistProgress;
  created_at: string;
  updated_at: string;
}

export interface CreativeRequestListItem {
  id: string;
  title: string;
  deliverable_type: CreativeDeliverableType;
  deliverable_type_display: string;
  status: CreativeRequestStatus;
  status_display: string;
  priority: CreativePriority;
  job_requirement_id: string;
  job_title: string;
  company_name: string;
  assigned_designer: UserMinimal | null;
  production_deadline: string | null;
  versions_count: number;
  active_version_number: number | null;
  active_version_status: AssetVersionStatus | null;
  active_version_checklist_progress: ChecklistProgress | null;
  is_archived: boolean;
  created_at: string;
}

export interface CreativeRequestDetail {
  id: string;
  title: string;
  deliverable_type: CreativeDeliverableType;
  deliverable_type_display: string;
  status: CreativeRequestStatus;
  status_display: string;
  priority: CreativePriority;
  brief: string;
  target_audience: string;
  registration_link: string;
  qr_code_target_url: string;
  contact_email: string;
  contact_phone: string;
  production_deadline: string | null;
  job_requirement_id: string;
  job_title: string;
  company_id: string;
  company_name: string;
  job_location: string;
  job_min_salary: string | null;
  job_max_salary: string | null;
  job_eligibility: string;
  job_deadline: string;
  job_interview_date: string | null;
  assigned_designer: UserMinimal | null;
  created_by: UserMinimal;
  versions: CreativeAssetVersion[];
  decisions: CreativeDecision[];
  is_editable: boolean;
  is_locked: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreativeMetrics {
  total_active: number;
  draft: number;
  assigned: number;
  in_production: number;
  review_pending: number;
  changes_requested: number;
  approved: number;
  urgent_deadlines_7_days: number;
}
