// Phase 11: Reports & Analytics Type Definitions

export interface CompanyReportsSummary {
  total_companies: number;
  total_job_drives: number;
  total_submissions: number;
  total_interviews: number;
  total_selections: number;
  total_offers: number;
  total_joinings: number;
  overall_selection_rate: number;
  overall_joining_rate: number;
  overall_average_ctc_lakhs: number;
  average_recruiter_rating: number | null;
}

export interface CompanyReportItem {
  company_id: string;
  company_name: string;
  tier: string;
  industry_domain: string;
  drives_count: number;
  submissions_count: number;
  interviews_count: number;
  selections_count: number;
  offers_count: number;
  joinings_count: number;
  min_ctc_lakhs: number;
  max_ctc_lakhs: number;
  avg_ctc_lakhs: number;
  recruiter_satisfaction_rating: number | null;
  selection_rate: number;
  joining_rate: number;
}

export interface CompanyReportsData {
  summary: CompanyReportsSummary;
  companies: CompanyReportItem[];
}

export interface CompanyReportsFilter {
  company_id?: string;
  tier?: string;
  industry_domain?: string;
  date_from?: string;
  date_to?: string;
}

export interface StudentReportsSummary {
  total_students: number;
  total_verified_academics: number;
  verification_rate: number;
  total_readiness_certified: number;
  readiness_certified_rate: number;
  total_applications: number;
  total_interview_participations: number;
  total_placed: number;
  placement_rate: number;
}

export interface DepartmentBreakdownItem {
  department: string;
  total_students: number;
  verified_count: number;
  certified_count: number;
  placed_count: number;
  placement_percentage: number;
}

export interface YearBreakdownItem {
  passing_year: number;
  total_students: number;
  placed_count: number;
  placement_percentage: number;
}

export interface DifficultyDistributionItem {
  difficulty_level: string;
  rating_count: number;
}

export interface StudentReportsData {
  summary: StudentReportsSummary;
  department_breakdown: DepartmentBreakdownItem[];
  year_breakdown: YearBreakdownItem[];
  difficulty_distribution: DifficultyDistributionItem[];
}

export interface StudentReportsFilter {
  department?: string;
  passing_year?: number;
  is_verified?: boolean;
  is_certified?: boolean;
  placed_only?: boolean;
}

export interface StudentSelfReportSummary {
  student_id: string;
  usn: string;
  full_name: string;
  department: string;
  passing_year: number;
  profile_completeness_percentage: number;
  academic_verification_status: string;
  is_readiness_certified: boolean;
  total_applications: number;
  total_shortlists: number;
  total_interviews: number;
  placement_result_status: string | null;
  has_offer: boolean;
  offer_status: string | null;
  joining_status: string | null;
  offered_ctc_lakhs: number | null;
}

export interface PlacementReportsSummary {
  total_placement_records: number;
  total_selected: number;
  total_rejected: number;
  total_waiting_list: number;
  total_hold: number;
  offers_accepted: number;
  offers_declined: number;
  offers_pending: number;
  offers_expired: number;
  joining_joined: number;
  joining_not_joined: number;
  joining_deferred: number;
  joining_pending: number;
  min_ctc_lakhs: number;
  max_ctc_lakhs: number;
  avg_ctc_lakhs: number;
  median_ctc_lakhs: number;
}

export interface CompanyPlacementItem {
  company_name: string;
  total_selected: number;
  offers_accepted: number;
  confirmed_joined: number;
  average_ctc_lakhs: number;
}

export interface PlacementReportsData {
  summary: PlacementReportsSummary;
  company_placements: CompanyPlacementItem[];
}

export interface PlacementReportsFilter {
  job_id?: string;
  company_id?: string;
  status?: string;
  offer_status?: string;
  joining_status?: string;
  date_from?: string;
  date_to?: string;
}

export interface FunnelStage {
  stage_number: number;
  stage_name: string;
  count: number;
  conversion_rate_from_prev: number;
  overall_conversion_rate: number;
}

export interface PerformanceReportsData {
  funnel: {
    stages: FunnelStage[];
    total_applications: number;
    total_joined: number;
    overall_pipeline_yield: number;
  };
}

export interface PerformanceReportsFilter {
  job_id?: string;
  company_id?: string;
  date_from?: string;
  date_to?: string;
}

export interface MonthlyMetrics {
  job_drives_posted: number;
  submissions_dispatched: number;
  interviews_conducted: number;
  results_received: number;
  candidates_selected: number;
  offers_accepted: number;
  joinings_confirmed: number;
  total_ctc_offered_lakhs: number;
}

export interface MonthlyTrendItem {
  month: number;
  job_drives_posted: number;
  candidates_selected: number;
  offers_accepted: number;
  joinings_confirmed: number;
}

export interface MonthlyStatisticsData {
  year: number;
  month: number;
  timezone: string;
  metrics: MonthlyMetrics;
  annual_trend: MonthlyTrendItem[];
}

export interface MonthlyStatisticsFilter {
  year?: number;
  month?: number;
}
