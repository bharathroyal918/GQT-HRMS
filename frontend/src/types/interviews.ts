/**
 * TypeScript Interfaces for Interview Management & Tracking (Phase 8 / Steps 29-35).
 */

export type ShortlistSource = "EMAIL" | "PORTAL" | "FILE_IMPORT" | "DIRECT_HANDOFF";

export type ShortlistedCandidateStatus =
  | "PENDING_SCHEDULE"
  | "SCHEDULED"
  | "IN_PROGRESS"
  | "COMPLETED"
  | "WITHDRAWN";

export type InterviewMode = "IN_PERSON" | "ONLINE" | "HYBRID";

export type ScheduleStatus = "SCHEDULED" | "RESCHEDULED" | "CONDUCTED" | "CANCELLED";

export type AttendanceStatus = "NO_RESPONSE" | "CONFIRMED" | "DECLINED" | "TENTATIVE";

export type AttendanceSource = "STUDENT_SELF_CONFIRMED" | "STAFF_RECORDED";

export type ConductedStatus =
  | "PENDING"
  | "CONDUCTED"
  | "NOT_CONDUCTED"
  | "CANDIDATE_ABSENT"
  | "INTERVIEWER_ABSENT"
  | "RESCHEDULED";

export type ReminderInterval = "HOURS_24" | "HOURS_2" | "MINUTES_30";

export type ReminderStatus = "SCHEDULED" | "PROCESSING" | "SENT" | "SKIPPED" | "CANCELLED" | "FAILED";

export type RoundCategory = "APTITUDE" | "CODING" | "TECHNICAL" | "HR" | "MANAGERIAL";

export type RoundStatus = "SCHEDULED" | "IN_PROGRESS" | "CLEARED" | "NOT_CLEARED" | "ON_HOLD" | "CANCELLED";

export type FollowUpResponseStatus = "RESPONSE_RECEIVED" | "AWAITING_RESPONSE" | "CALLBACK_REQUESTED";

export interface SubmittableCandidate {
  submission_id: string;
  package_id: string;
  package_title: string;
  student_id: string;
  roll_number: string;
  full_name: string;
  email: string;
  phone_number: string;
  department: string;
  degree: string;
  cgpa: number;
  submission_status: string;
  is_already_shortlisted: boolean;
}

export interface ShortlistedCandidateItem {
  id: string;
  student_id: string;
  roll_number: string;
  full_name: string;
  email: string;
  phone_number: string;
  department: string;
  degree: string;
  cgpa: number;
  status: ShortlistedCandidateStatus;
  recruiter_notes: string;
  active_schedule_id: string | null;
  created_at: string;
}

export interface CandidateShortlist {
  id: string;
  job_requirement: string;
  company: string;
  company_name: string;
  job_title: string;
  hr_contact: string;
  hr_contact_name: string;
  submission_package: string | null;
  shortlist_reference_code: string;
  source: ShortlistSource;
  received_at: string;
  candidate_count: number;
  notes: string;
  created_by: string;
  created_by_name: string;
  candidates: ShortlistedCandidateItem[];
  created_at: string;
}

export interface CandidateShortlistCreatePayload {
  job_id: string;
  company_id: string;
  hr_contact_id: string;
  submission_package_id?: string | null;
  student_ids: string[];
  source?: ShortlistSource;
  received_at?: string | null;
  notes?: string;
}

export interface InterviewReminderItem {
  id: string;
  interval: ReminderInterval;
  interval_display: string;
  scheduled_for: string;
  status: ReminderStatus;
  status_display: string;
  sent_at: string | null;
  channel: string;
  provider_message_id: string;
  error_message: string;
  attempt_count: number;
}

export interface InterviewNotificationLogItem {
  id: string;
  recipient_email: string;
  recipient_phone: string;
  channel: string;
  status: string;
  provider_message_id: string;
  details_payload: Record<string, any>;
  sent_at: string;
  sent_by: string;
  sent_by_name: string;
}

export interface InterviewSchedule {
  id: string;
  job_requirement: string;
  company: string;
  company_name: string;
  job_title: string;
  candidate: string;
  student: string;
  candidate_roll: string;
  candidate_name: string;
  candidate_email: string;
  candidate_phone: string;
  schedule_reference_code: string;
  mode: InterviewMode;
  mode_display: string;
  interview_date: string;
  interview_time: string;
  scheduled_start_time: string;
  venue: string;
  meeting_link: string;
  required_documents: string;
  status: ScheduleStatus;
  status_display: string;
  rescheduled_from: string | null;
  is_superseded: boolean;
  notified_at: string | null;
  notification_status: "NOT_SENT" | "SENT" | "FAILED";
  attendance_status: AttendanceStatus;
  attendance_status_display: string;
  attendance_confirmed_at: string | null;
  attendance_confirmed_by: string | null;
  attendance_confirmed_by_name: string;
  attendance_source: AttendanceSource;
  attendance_notes: string;
  conducted_status: ConductedStatus;
  conducted_status_display: string;
  conducted_at: string | null;
  conducted_recorded_by: string | null;
  conducted_recorded_by_name: string;
  conducted_notes: string;
  created_by: string;
  created_by_name: string;
  reminders: InterviewReminderItem[];
  notification_logs: InterviewNotificationLogItem[];
  created_at: string;
}

export interface InterviewScheduleCreatePayload {
  candidate_id: string;
  interview_date: string;
  interview_time: string;
  mode?: InterviewMode;
  venue?: string;
  meeting_link?: string;
  required_documents?: string;
}

export interface InterviewReschedulePayload {
  new_date: string;
  new_time: string;
  new_mode?: InterviewMode;
  new_venue?: string;
  new_meeting_link?: string;
  new_required_documents?: string;
  reschedule_reason?: string;
}

export interface AttendanceConfirmationPayload {
  attendance_status: "CONFIRMED" | "DECLINED" | "TENTATIVE";
  notes?: string;
}

export interface InterviewConductedPayload {
  conducted_status: ConductedStatus;
  notes?: string;
}

export interface InterviewRound {
  id: string;
  job_requirement: string;
  company: string;
  company_name: string;
  job_title: string;
  candidate: string;
  candidate_roll: string;
  candidate_name: string;
  schedule: string | null;
  round_number: number;
  category: RoundCategory;
  category_display: string;
  round_name: string;
  status: RoundStatus;
  status_display: string;
  scheduled_date: string | null;
  scheduled_time: string | null;
  interviewer_names: string;
  internal_staff_notes?: string;
  evaluated_at: string | null;
  evaluated_by: string | null;
  evaluated_by_name: string;
  created_by: string;
  created_by_name: string;
  created_at: string;
}

export interface InterviewRoundCreatePayload {
  candidate_id: string;
  category: RoundCategory;
  round_name?: string;
  scheduled_date?: string | null;
  scheduled_time?: string | null;
  interviewer_names?: string;
  internal_staff_notes?: string;
  schedule_id?: string | null;
}

export interface InterviewRoundEvaluatePayload {
  status: "CLEARED" | "NOT_CLEARED" | "ON_HOLD";
  internal_staff_notes?: string;
}

export interface HRInterviewFollowUp {
  id: string;
  job_requirement: string;
  company: string;
  company_name: string;
  job_title: string;
  hr_contact: string;
  hr_contact_name: string;
  follow_up_date: string;
  channel: string;
  channel_display: string;
  conducted_by: string;
  conducted_by_name: string;
  candidate_status_reported: string;
  pending_rounds: string;
  expected_result_date: string | null;
  is_date_confirmed: boolean;
  next_follow_up_date: string | null;
  response_status: FollowUpResponseStatus;
  response_status_display: string;
  hr_response_summary: string;
  notes: string;
  created_at: string;
}

export interface HRInterviewFollowUpCreatePayload {
  job_id: string;
  company_id: string;
  hr_contact_id: string;
  candidate_status_reported: string;
  pending_rounds?: string;
  expected_result_date?: string | null;
  is_date_confirmed?: boolean;
  next_follow_up_date?: string | null;
  channel?: string;
  response_status?: FollowUpResponseStatus;
  hr_response_summary?: string;
  notes?: string;
}

export interface InterviewKPIs {
  total_shortlists: number;
  total_shortlisted_candidates: number;
  total_schedules: number;
  confirmed_attendance: number;
  interviews_conducted: number;
  pending_hr_followups: number;
}
