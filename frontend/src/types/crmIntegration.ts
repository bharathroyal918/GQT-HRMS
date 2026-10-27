export type CRMConflictSeverity = 'CRITICAL' | 'WARNING' | 'INFO';

export type CRMDatabaseHealthStatus = 'HEALTHY' | 'NEEDS_ATTENTION' | 'CRITICAL';

export interface CRMConflict {
  area: string;
  severity: CRMConflictSeverity;
  resource_type: string;
  resource_id: string;
  description: string;
  recommended_action: string;
}

export interface CRMDatabaseHealthSummary {
  total_records_checked: number;
  total_consistent_records: number;
  total_conflicts: number;
  health_score_percentage: number;
  status: CRMDatabaseHealthStatus;
  as_of: string;
}

export interface CRMDatabaseHealthArea {
  name: string;
  total: number;
  consistent: number;
  conflicts: number;
  status: 'CLEAN' | 'WARNING' | 'CRITICAL';
}

export interface CRMDatabaseHealthReport {
  summary: CRMDatabaseHealthSummary;
  areas: Record<string, CRMDatabaseHealthArea>;
  conflicts: CRMConflict[];
}

export interface CRMReconciliationRun {
  id: string;
  triggered_by: string | null;
  triggered_by_name: string;
  triggered_by_email: string;
  status: 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  total_records_checked: number;
  conflicts_detected: number;
  records_synchronized: number;
  diagnostic_details: Record<string, unknown>;
  summary: string;
  created_at: string;
}

export interface CRMReconciliationSyncResponse {
  success: boolean;
  message: string;
  data: {
    run_id: string;
    dry_run: boolean;
    records_synchronized: number;
    conflicts_detected: number;
    health_score_percentage: number;
    diagnostics: CRMDatabaseHealthReport;
  };
}

export interface CommunicationTimelineEvent {
  id: string;
  category: string;
  channel: string;
  channel_display?: string | null;
  direction: 'OUTBOUND' | 'INBOUND' | 'SYSTEM';
  subject: string;
  summary: string;
  actor_name: string | null;
  contact_name?: string | null;
  status: string;
  timestamp: string;
}

export interface Company360Profile {
  company: {
    id: string;
    name: string;
    domain: string;
    domain_category: string;
    tier: string;
    relationship_status: string;
    relationship_status_display: string;
    city: string;
    state: string;
    owner_name: string | null;
  };
  hr_contacts: Array<{
    id: string;
    name: string;
    designation: string;
    department: string;
    email: string;
    phone: string;
    preferred_channel: string;
    status: string;
  }>;
  lifetime_metrics: {
    total_jobs: number;
    total_submissions: number;
    total_interviewed: number;
    total_placed: number;
    total_joined: number;
    avg_offered_ctc: number;
    total_hr_feedbacks: number;
    total_student_feedbacks: number;
  };
  feedback_summary: {
    total_hr_evaluations: number;
    avg_technical_skills_rating: number;
    avg_communication_skills_rating: number;
    avg_hiring_satisfaction_rating: number;
    difficulty_breakdown: Record<string, number>;
  };
  recruitment_drives: Array<{
    id: string;
    title: string;
    status: string;
    openings_count: number;
    interview_date: string | null;
    placed_count: number;
    created_at: string;
  }>;
  placed_candidates: Array<{
    id: string;
    student_id: string;
    student_name: string;
    student_roll_number: string;
    job_title: string;
    designation_offered: string;
    offered_ctc: number | null;
    acceptance_status: string;
    joining_status: string;
    status_updated_at: string | null;
  }>;
}

export interface Student360Profile {
  student: {
    id: string;
    roll_number: string;
    full_name: string;
    institutional_email: string;
    department: string;
    degree: string;
    college_name: string;
    cgpa: number | null;
    active_backlogs: number;
    graduation_year: number;
    is_verified_by_placement: boolean;
  };
  readiness_gate: {
    is_certified: boolean;
    certified_at: string | null;
    comments: string;
  };
  resumes: Array<{
    id: string;
    version_number: number;
    file_name: string;
    file_size_bytes: number;
    is_current: boolean;
    created_at: string;
  }>;
  overall_placement_outcome: string;
  placement_history: Array<{
    id: string;
    company_name: string;
    job_title: string;
    status: string;
    status_display: string;
    designation_offered: string;
    offered_ctc: number | null;
    acceptance_status: string;
    joining_status: string;
    status_updated_at: string | null;
  }>;
  applications: Array<{
    id: string;
    job_title: string;
    company_name: string;
    status: string;
    created_at: string;
  }>;
  submissions: Array<{
    id: string;
    company_name: string;
    job_title: string;
    status: string;
    status_display: string;
    created_at: string;
  }>;
  trainer_evaluations: Array<{
    id: string;
    trainer_name: string;
    student_readiness: string;
    student_readiness_display: string;
    training_effectiveness_rating: number;
    areas_for_improvement: string;
    created_at: string;
  }>;
}
