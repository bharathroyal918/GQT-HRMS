/**
 * TypeScript Interfaces for Placement Management & Tracking (Phase 8 / Steps 36-41).
 */

export type ResultIntakeSource =
  | "EMAIL"
  | "PORTAL"
  | "SPREADSHEET_IMPORT"
  | "DIRECT_HANDOFF";

export type CandidatePlacementStatusType =
  | "SELECTED"
  | "REJECTED"
  | "WAITING_LIST"
  | "HOLD";

export type OfferAcceptanceStatus =
  | "PENDING_RESPONSE"
  | "ACCEPTED"
  | "DECLINED"
  | "EXPIRED";

export type JoiningStatus =
  | "NOT_APPLICABLE"
  | "PENDING_JOINING"
  | "JOINED"
  | "NOT_JOINED"
  | "DEFERRED";

export interface PlacementStatusHistory {
  id: string;
  previous_status: CandidatePlacementStatusType;
  new_status: CandidatePlacementStatusType;
  reason: string;
  changed_by_name: string;
  created_at: string;
}

export interface PlacementNotificationLog {
  id: string;
  recipient_email: string;
  recipient_phone: string;
  channel: string;
  status: string;
  status_announced: string;
  provider_message_id: string;
  details_payload: Record<string, any>;
  sent_at: string;
  sent_by_name: string;
}

export interface OfferLetterVersion {
  id: string;
  version_number: number;
  file_name: string;
  file_size_bytes: number;
  sha256_hash: string;
  superseded_at: string;
  superseded_by_name: string;
  superseded_reason: string;
}

export interface CandidateOfferLetter {
  id: string;
  file_name: string;
  file_size_bytes: number;
  sha256_hash: string;
  version_number: number;
  is_active: boolean;
  issued_at: string;
  issued_by_name: string;
  acceptance_deadline: string | null;
  acceptance_status: OfferAcceptanceStatus;
  acceptance_status_display: string;
  accepted_at: string | null;
  acceptance_source: string;
  student_decision_notes: string;
  joining_status: JoiningStatus;
  joining_status_display: string;
  expected_joining_date: string | null;
  actual_joining_date: string | null;
  deferred_joining_date: string | null;
  joining_location: string;
  employee_id_assigned: string;
  joining_notes: string;
  joining_verified_at: string | null;
  download_url: string;
  created_at: string;
}

export interface CandidatePlacementStatus {
  id: string;
  job_requirement: string;
  job_title: string;
  company: string;
  company_name: string;
  student: string;
  student_roll: string;
  student_name: string;
  student_email: string;
  status: CandidatePlacementStatusType;
  status_display: string;
  designation_offered: string;
  offered_ctc: string | null;
  work_location: string;
  remarks: string;
  has_offer_letter: boolean;
  offer_letter_id: string | null;
  acceptance_status: OfferAcceptanceStatus | null;
  joining_status: JoiningStatus | null;
  status_updated_at: string;
  status_updated_by_name: string;
  created_at: string;
  history?: PlacementStatusHistory[];
  offer_letter?: CandidateOfferLetter | null;
}

export interface FinalResultIntake {
  id: string;
  job_requirement: string;
  job_title: string;
  company: string;
  company_name: string;
  hr_contact: string | null;
  hr_contact_name: string;
  result_reference_code: string;
  source: ResultIntakeSource;
  source_display: string;
  received_at: string;
  total_results: number;
  selected_count: number;
  rejected_count: number;
  waiting_list_count: number;
  hold_count: number;
  notes: string;
  created_at: string;
  created_by_name: string;
}

export interface PlacementKPIs {
  total_results: number;
  selected_count: number;
  rejected_count: number;
  waiting_list_count: number;
  hold_count: number;
  total_offers: number;
  offers_accepted: number;
  offers_declined: number;
  offers_pending: number;
  total_joined: number;
  total_deferred: number;
  total_not_joined: number;
}

export interface ParticipatingCandidate {
  student_id: string;
  roll_number: string;
  student_name: string;
  institutional_email: string;
  department: string;
  degree: string;
  cgpa: number | null;
  existing_placement_status: string | null;
}

export interface IngestCandidateResultItem {
  student_id: string;
  status: CandidatePlacementStatusType;
  designation_offered?: string;
  offered_ctc?: number | null;
  work_location?: string;
  remarks?: string;
}

export interface FinalResultIntakePayload {
  job_requirement_id: string;
  company_id: string;
  hr_contact_id?: string | null;
  source?: ResultIntakeSource;
  received_at?: string | null;
  notes?: string;
  candidate_results: IngestCandidateResultItem[];
}

export interface UpdatePlacementStatusPayload {
  status: CandidatePlacementStatusType;
  reason?: string;
  designation_offered?: string;
  offered_ctc?: number | null;
  work_location?: string;
  remarks?: string;
}

export interface OfferAcceptancePayload {
  decision: "ACCEPTED" | "DECLINED";
  notes?: string;
  source?: "STUDENT_PORTAL" | "PLACEMENT_OFFICE";
}

export interface JoiningStatusUpdatePayload {
  joining_status: "JOINED" | "NOT_JOINED" | "DEFERRED";
  actual_joining_date?: string | null;
  deferred_joining_date?: string | null;
  joining_location?: string;
  employee_id_assigned?: string;
  notes?: string;
}
