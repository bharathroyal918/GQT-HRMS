/**
 * TypeScript Type Definitions for Phase 13: Continuous Improvement
 * Covers:
 * 1. Placement Rate Analytics & Funnel Breakdown
 * 2. Feedback Intelligence & Anonymized Aggregations
 * 3. Evidence-Based Skill Gap Matrix
 * 4. Remedial & Strategic Training Plans
 * 5. Recruitment Cycle Reviews & Continuous Action Tracking
 * 6. Continuous Improvement Data Diagnostics
 */

// ----------------------------------------------------------------------------
// Capability A: Placement Rate Analytics
// ----------------------------------------------------------------------------
export interface PlacementRateFilter {
  cohort_year?: number;
  department?: string;
  college_name?: string;
  company_id?: string;
  job_requirement_id?: string;
  start_date?: string;
  end_date?: string;
}

export interface PlacementRateSummary {
  total_cohort_students: number;
  total_eligible_students: number;
  distinct_students_applied: number;
  total_applications: number;
  distinct_students_submitted: number;
  distinct_students_shortlisted: number;
  distinct_students_interviewed: number;
  distinct_students_selected: number;
  total_selections: number;
  single_offer_students: number;
  dual_offer_students: number;
  multi_offer_students: number;
  total_offers_issued: number;
  total_offers_accepted: number;
  total_offers_declined: number;
  total_offers_pending: number;
  distinct_students_joined: number;
  distinct_students_not_joined: number;
  distinct_students_pending_outcomes: number;
  placement_rate_eligible: number;
  placement_rate_applicants: number;
  interview_selection_rate: number;
  offer_acceptance_rate: number;
  joining_rate: number;
  overall_pipeline_yield: number;
}

export interface DepartmentBreakdown {
  department: string;
  total_students: number;
  applied_students: number;
  selected_students: number;
  joined_students: number;
  placement_rate: number;
}

export interface MetricDefinition {
  metric_name: string;
  percentage: number;
  numerator: number;
  numerator_label: string;
  denominator: number;
  denominator_label: string;
  formula: string;
  records_count: number;
  notes: string;
}

export interface PlacementRateResponse {
  filters_applied: PlacementRateFilter;
  summary: PlacementRateSummary;
  department_breakdown: DepartmentBreakdown[];
  metric_definitions: MetricDefinition[];
  generated_at: string;
}

// ----------------------------------------------------------------------------
// Capability B: Feedback Intelligence
// ----------------------------------------------------------------------------
export interface FeedbackIntelligenceFilter {
  company_id?: string;
  job_requirement_id?: string;
  cohort_year?: number;
  start_date?: string;
  end_date?: string;
}

export interface FeedbackKpiSummary {
  total_recruiter_evaluations: number;
  total_student_experiences: number;
  total_trainer_assessments: number;
  avg_recruiter_tech_rating: number;
  avg_recruiter_comm_rating: number;
  avg_recruiter_satisfaction: number;
  avg_trainer_effectiveness: number;
}

export interface DifficultyBreakdown {
  difficulty: string;
  count: number;
  percentage: number;
}

export interface ReadinessBreakdown {
  readiness: string;
  count: number;
  percentage: number;
}

export interface RecruiterRemark {
  id: string;
  company_name: string;
  role_title: string;
  category: string;
  remark: string;
  rating: number;
  date: string;
}

export interface StudentSuggestion {
  id: string;
  company_name: string;
  difficulty: string;
  suggestion: string;
  interview_experience: string;
  date: string;
  is_anonymous: boolean;
}

export interface TrainerImprovementArea {
  id: string;
  student_name: string;
  readiness: string;
  areas_for_improvement: string;
  effectiveness_rating: number;
  date: string;
}

export interface FeedbackIntelligenceResponse {
  anonymity_rule_enforced: boolean;
  minimum_group_threshold: number;
  is_small_group_masked?: boolean;
  kpi_summary: FeedbackKpiSummary;
  recruiter_ratings: {
    avg_technical: number;
    avg_communication: number;
    avg_satisfaction: number;
    distribution_quality: Record<string, number>;
  };
  student_difficulty_breakdown: DifficultyBreakdown[];
  trainer_readiness_breakdown: ReadinessBreakdown[];
  recruiter_remarks_sample: RecruiterRemark[];
  student_suggestions_sample: StudentSuggestion[];
  trainer_improvement_areas_sample: TrainerImprovementArea[];
  anonymity_notice?: string;
  hr_feedback?: {
    total_responses: number;
    avg_technical_rating: number;
    avg_communication_rating: number;
    avg_hiring_satisfaction: number;
    candidate_quality_distribution: Record<string, number>;
    recent_observations: Array<{
      company_name: string;
      candidate_quality: string;
      technical_rating: number;
      communication_rating: number;
      satisfaction_rating: number;
      remarks: string;
      date: string;
    }>;
  };
  student_feedback?: {
    total_responses: number;
    difficulty_distribution: Record<string, number>;
    is_small_group_masked: boolean;
    anonymity_threshold: number;
    recent_experiences: Array<any>;
  };
  trainer_feedback?: {
    total_evaluations: number;
    avg_training_effectiveness: number;
    readiness_distribution: Record<string, number>;
    recurring_improvement_areas: Array<any>;
  };
  generated_at: string;
}

// ----------------------------------------------------------------------------
// Capability C: Skill Gap Matrix
// ----------------------------------------------------------------------------
export interface SkillGapFilter {
  domain_track?: string;
  cohort_year?: number;
}

export type SkillCoverageCategory =
  | 'EVALUATED_WELL'
  | 'UNASSESSED_DEMAND'
  | 'CRITICAL_GAP'
  | 'SUFFICIENT_EVIDENCE'
  | 'MODERATE_GAP'
  | 'STRENGTH'
  | 'MONITORING';

export interface SkillGapItem {
  skill: string;
  skill_name?: string;
  jobs_requiring: number;
  market_demand_jobs_count?: number;
  companies_requiring: number;
  jobs_referencing?: string[];
  assessment_tests_count: number;
  total_attempts: number;
  assessment_attempts_count?: number;
  passed_attempts: number;
  pass_percentage: number;
  assessment_pass_rate?: number | null;
  average_assessment_score?: number | null;
  student_skill_profiles_count?: number;
  mock_evaluations_count?: number;
  hr_feedback_count?: number;
  coverage_category: SkillCoverageCategory;
  gap_status?: string;
  data_coverage_level?: string;
  status_label?: string;
  severity?: string;
  recommendation: string;
  evidence_based_recommendation?: string;
}

export interface SkillGapSummary {
  total_skills_evaluated: number;
  critical_gaps_count: number;
  unassessed_demand_count: number;
  moderate_gaps_count: number;
  strengths_count: number;
  total_jobs_analyzed: number;
  total_assessment_attempts_analyzed: number;
  total_mock_evaluations_analyzed: number;
  mock_benchmarks?: {
    avg_technical_competence: number;
    avg_problem_solving: number;
    avg_communication_clarity: number;
  };
}

export interface SkillGapMatrixResponse {
  ai_disclaimer: string;
  methodology_disclaimer?: string;
  total_market_demand_skills: number;
  total_assessed_skills: number;
  unassessed_high_demand_skills: number;
  critical_gap_skills: number;
  summary?: SkillGapSummary;
  skill_matrix: SkillGapItem[];
  generated_at: string;
}

// ----------------------------------------------------------------------------
// Capability D: Training Plans
// ----------------------------------------------------------------------------
export type TrainingPlanStatus =
  | 'DRAFT'
  | 'PROPOSED'
  | 'APPROVED'
  | 'SCHEDULED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';

export interface TrainingPlan {
  id: string;
  title: string;
  plan_code: string;
  target_skill: string;
  evidence_rationale: string;
  motivation_evidence?: string;
  target_cohort?: string;
  target_cohort_year?: number | null;
  target_department?: string;
  target_eligible_count?: number;
  enrolled_students_count?: number;
  proposed_objectives: string;
  planned_sessions_count?: number;
  planned_activities?: string;
  responsible_trainer?: string | null;
  responsible_trainer_id?: string;
  responsible_trainer_name: string;
  planned_start_date?: string | null;
  planned_end_date?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  expected_outcome: string;
  status: TrainingPlanStatus;
  status_display?: string;
  approved_by?: string | null;
  approved_by_name: string | null;
  approved_at?: string | null;
  approval_notes: string;
  actual_completion_results: string;
  cancellation_reason?: string;
  created_by?: string | null;
  created_by_name: string;
  created_at: string;
  updated_at: string;
  linked_actions_count?: number;
}

export interface TrainingPlanSummary {
  total_plans: number;
  status_counts: Record<string, number>;
}

export interface TrainingPlansResponse {
  summary: TrainingPlanSummary;
  training_plans: TrainingPlan[];
  generated_at: string;
}

export interface TrainingPlanCreatePayload {
  title: string;
  target_skill: string;
  evidence_rationale: string;
  target_cohort_year?: number | null;
  target_department?: string;
  proposed_objectives: string;
  planned_activities?: string;
  responsible_trainer?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  expected_outcome?: string;
}

export interface TrainingPlanTransitionPayload {
  status: TrainingPlanStatus;
  approval_notes?: string;
  actual_completion_results?: string;
}

// ----------------------------------------------------------------------------
// Capability E: Recruitment Cycle Reviews
// ----------------------------------------------------------------------------
export type RecruitmentCycleStatus =
  | 'ACTIVE'
  | 'UNDER_REVIEW'
  | 'COMPLETED'
  | 'ARCHIVED';

export type CycleActionCategory =
  | 'CURRICULUM_TRAINING'
  | 'INTERVIEW_PREP'
  | 'CORPORATE_OUTREACH'
  | 'STUDENT_POLICY'
  | 'ASSESSMENT_UPGRADE';

export type CycleActionStatus =
  | 'PLANNED'
  | 'IN_PROGRESS'
  | 'VERIFIED'
  | 'DROPPED';

export interface CycleImprovementAction {
  id: string;
  cycle_review: string;
  cycle_review_id?: string;
  title: string;
  category: CycleActionCategory;
  action_description: string;
  success_criteria: string;
  owner?: string | null;
  owner_name: string;
  due_date?: string | null;
  status: CycleActionStatus;
  outcome_notes: string;
  created_at: string;
  updated_at: string;
}

export interface RecruitmentCycleReview {
  id: string;
  cycle_name: string;
  cycle_code: string;
  academic_year: string;
  status: RecruitmentCycleStatus;
  period_start?: string | null;
  period_end?: string | null;
  baseline_metrics_snapshot: Record<string, any>;
  goals_and_targets: string;
  review_summary: string;
  lead_reviewer?: string | null;
  lead_reviewer_name: string;
  total_actions: number;
  completed_actions: number;
  action_items?: CycleImprovementAction[];
  created_at: string;
  updated_at: string;
}

export interface RecruitmentCycleReviewCreatePayload {
  cycle_name: string;
  academic_year: string;
  period_start?: string | null;
  period_end?: string | null;
  goals_and_targets?: string;
  review_summary?: string;
  capture_current_baseline?: boolean;
}

export interface CycleImprovementActionCreatePayload {
  cycle_review_id: string;
  title: string;
  category: CycleActionCategory;
  action_description: string;
  success_criteria?: string;
  owner?: string | null;
  due_date?: string | null;
}

// ----------------------------------------------------------------------------
// Diagnostics: Data Quality Integrity
// ----------------------------------------------------------------------------
export interface DiagnosticCheckItem {
  code: string;
  name: string;
  status: 'PASS' | 'WARNING' | 'FAIL';
  count: number;
  message: string;
  impact: string;
  actionable_guidance: string;
}

export interface ContinuousImprovementDiagnosticsResponse {
  overall_health: 'HEALTHY' | 'ACTION_REQUIRED' | 'NEEDS_ATTENTION';
  overall_score: number;
  checks: DiagnosticCheckItem[];
  timestamp: string;
}
