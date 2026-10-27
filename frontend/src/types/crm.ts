export type CompanyDomainCategory =
  | 'IT_SERVICES'
  | 'PRODUCT_TECH'
  | 'CORE_ENGINEERING'
  | 'FINANCE_BANKING'
  | 'BPO_ITES'
  | 'EDTECH'
  | 'HEALTHCARE'
  | 'CONSULTING'
  | 'OTHER';

export type CompanyTier = 'TIER_1' | 'TIER_2' | 'TIER_3';

export type CompanyRelationshipStatus =
  | 'DISCOVERED'
  | 'OUTREACH_IN_PROGRESS'
  | 'CONNECTED'
  | 'INTERESTED'
  | 'ACTIVE_HIRING_PARTNER'
  | 'NOT_INTERESTED'
  | 'ON_HOLD';

export type CompanyDiscoverySource =
  | 'MARKET_RESEARCH'
  | 'LINKEDIN'
  | 'REFERRAL'
  | 'CAMPUS_INBOUND'
  | 'COLD_OUTREACH'
  | 'JOB_BOARD'
  | 'OTHER';

export type OutreachChannel =
  | 'CALL'
  | 'EMAIL'
  | 'LINKEDIN'
  | 'WHATSAPP'
  | 'IN_PERSON'
  | 'OTHER';

export type OutreachOutcome =
  | 'CONNECTED_INTERESTED'
  | 'CONNECTED_NOT_INTERESTED'
  | 'CONNECTED_CALL_LATER'
  | 'NO_ANSWER_BUSY'
  | 'INVALID_CONTACT_DETAILS'
  | 'GATEKEEPER_BLOCKED'
  | 'FOLLOW_UP_SCHEDULED'
  | 'REQUIREMENT_COLLECTED';

export type FollowUpPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type FollowUpStatus = 'OPEN' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

export interface UserMinimal {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
}

export interface CompanyMinimal {
  id: string;
  name: string;
  domain_category: CompanyDomainCategory;
  relationship_status: CompanyRelationshipStatus;
}

export interface CompanyListItem {
  id: string;
  name: string;
  normalized_name: string;
  website: string;
  domain: string;
  domain_category: CompanyDomainCategory;
  tier: CompanyTier;
  relationship_status: CompanyRelationshipStatus;
  source: CompanyDiscoverySource;
  city: string;
  state: string;
  country: string;
  owner: UserMinimal | null;
  hr_contacts_count: number;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface HRContactSummary {
  id: string;
  name: string;
  designation: string;
  email: string;
  phone: string;
  status: string;
  is_archived: boolean;
}

export interface CompanyDetail extends CompanyListItem {
  address: string;
  notes: string;
  created_by: UserMinimal | null;
  updated_by: UserMinimal | null;
  hr_contacts: HRContactSummary[];
  recent_outreach_count: number;
  open_follow_ups_count: number;
}

export interface DuplicateMatch {
  company_id: string;
  name: string;
  domain: string;
  relationship_status: string;
  is_archived: boolean;
  match_type: 'EXACT_NAME' | 'DOMAIN_MATCH';
  reason: string;
}

export interface HRContactListItem {
  id: string;
  company: CompanyMinimal;
  name: string;
  designation: string;
  department: string;
  email: string;
  phone: string;
  alt_phone: string;
  linkedin_url: string;
  preferred_channel: OutreachChannel;
  status: string;
  owner: UserMinimal | null;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface HRContactDetail extends HRContactListItem {
  notes: string;
  created_by: UserMinimal | null;
  updated_by: UserMinimal | null;
}

export interface OutreachLogItem {
  id: string;
  company: CompanyMinimal;
  hr_contact: HRContactSummary | null;
  performed_by: UserMinimal;
  channel: OutreachChannel;
  direction: 'OUTBOUND' | 'INBOUND';
  activity_date: string;
  outcome: OutreachOutcome;
  subject: string;
  notes: string;
  followup_required: boolean;
  correlation_id: string;
  created_at: string;
}

export type FollowUpCategory =
  | 'HR_OUTREACH'
  | 'STUDENT_RECONNECT'
  | 'INTERVIEW_CONFIRMATION'
  | 'OFFER_ACCEPTANCE'
  | 'JOINING_CHECK'
  | 'GENERAL_RECONNECT';

export type ReminderChannel = 'EMAIL' | 'WHATSAPP' | 'BOTH' | 'NONE';

export type ReminderDeliveryStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'SENT'
  | 'DELIVERED'
  | 'FAILED'
  | 'RETRY_SCHEDULED'
  | 'CANCELLED';

export type StaffNotificationType =
  | 'FOLLOW_UP_DUE'
  | 'FOLLOW_UP_OVERDUE'
  | 'COMMUNICATION_FAILED'
  | 'CASE_ESCALATED'
  | 'SYSTEM_ALERT';

export type CaseEscalationType = 'OVERDUE_FOLLOW_UP' | 'UNRESOLVED_COMMUNICATION_FAILURE';

export type CaseEscalationStatus = 'PENDING' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export type CaseEscalationLevel = 'LEVEL_1' | 'LEVEL_2';

export interface FollowUpItem {
  id: string;
  company: CompanyMinimal;
  hr_contact: HRContactSummary | null;
  assigned_to: UserMinimal;
  category?: FollowUpCategory;
  student?: string | null;
  student_name?: string | null;
  student_roll_number?: string | null;
  job_requirement?: string | null;
  job_title?: string | null;
  interview_schedule?: string | null;
  placement_status?: string | null;
  due_date: string;
  priority: FollowUpPriority;
  status: FollowUpStatus;
  purpose: string;
  notes?: string;
  remind_at?: string | null;
  reminder_channel?: ReminderChannel;
  reminders_count?: number;
  is_overdue: boolean;
  rescheduled_count: number;
  completion_notes: string;
  completed_at: string | null;
  completed_by: UserMinimal | null;
  cancellation_reason: string;
  created_by: UserMinimal | null;
  created_at: string;
  updated_at: string;
}

export interface FollowUpReminderItem {
  id: string;
  follow_up: string;
  follow_up_purpose: string;
  company_name: string;
  channel: 'EMAIL' | 'WHATSAPP';
  recipient: string;
  recipient_name: string;
  scheduled_for: string;
  status: ReminderDeliveryStatus;
  attempt_count: number;
  max_attempts: number;
  backoff_until: string | null;
  sent_at: string | null;
  delivered_at: string | null;
  provider_message_id: string;
  error_message: string;
  is_simulated: boolean;
  created_at: string;
  updated_at: string;
}

export interface StaffNotification {
  id: string;
  recipient: string;
  notification_type: StaffNotificationType;
  title: string;
  message: string;
  link: string;
  follow_up: string | null;
  company_name: string | null;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
}

export interface CaseEscalation {
  id: string;
  case_type: CaseEscalationType;
  follow_up: string | null;
  company_name: string | null;
  follow_up_purpose: string | null;
  follow_up_due_date: string | null;
  escalated_to: string;
  escalated_to_name: string | null;
  escalated_to_email: string | null;
  escalated_by: string | null;
  previous_assigned_to: string | null;
  previous_assigned_to_name: string | null;
  reason: string;
  escalation_level: CaseEscalationLevel;
  status: CaseEscalationStatus;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  acknowledged_by_name: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolved_by_name: string | null;
  resolution_notes: string;
  created_at: string;
  updated_at: string;
}

export interface AutomationRunResult {
  success: boolean;
  dry_run: boolean;
  correlation_id: string;
  executed_at: string;
  reminders_processed?: number;
  notifications_created?: number;
  escalations_created?: number;
  reminders_eligible?: number;
  due_notifications_eligible?: number;
  overdue_escalations_eligible?: number;
}

export interface CRMMetrics {
  total_active_companies: number;
  total_active_contacts: number;
  daily_outreach_target: number;
  today_outreach_count: number;
  today_outreach_progress_percent: number;
  channel_breakdown: Record<string, number>;
  user_today_outreach_count: number;
  follow_ups_due_today: number;
  follow_ups_overdue: number;
  follow_ups_completed: number;
  timezone: string;
  as_of: string;
  recent_activities: Array<{
    id: string;
    channel: OutreachChannel;
    direction: string;
    activity_date: string;
    outcome: OutreachOutcome;
    subject: string;
    company__id: string;
    company__name: string;
    hr_contact__id: string | null;
    hr_contact__name: string | null;
    performed_by__email: string;
    performed_by__first_name: string;
    performed_by__last_name: string;
  }>;
}

export interface PaginatedResponse<T> {
  success: boolean;
  meta: {
    count: number;
    total_pages: number;
    current_page: number;
    next: string | null;
    previous: string | null;
  };
  data: T[];
}
