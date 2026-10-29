import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ContinuousImprovementHubPage } from '../pages/improvement/ContinuousImprovementHubPage';
import { AuthProvider } from '../context/AuthContext';
import { continuousImprovementApi } from '../api/continuousImprovementApi';

vi.mock('../api/continuousImprovementApi', () => ({
  continuousImprovementApi: {
    getPlacementRate: vi.fn(),
    exportPlacementRateCsv: vi.fn(),
    getFeedbackIntelligence: vi.fn(),
    getSkillGapMatrix: vi.fn(),
    exportSkillGapCsv: vi.fn(),
    getTrainingPlans: vi.fn(),
    createTrainingPlan: vi.fn(),
    transitionTrainingPlan: vi.fn(),
    exportTrainingPlansCsv: vi.fn(),
    getCycleReviews: vi.fn(),
    createCycleReview: vi.fn(),
    createCycleAction: vi.fn(),
    updateCycleActionStatus: vi.fn(),
    getDiagnostics: vi.fn(),
  },
  downloadCsvBlob: vi.fn(),
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

const mockPlacementData = {
  filters_applied: { cohort_year: 2026 },
  summary: {
    total_cohort_students: 3,
    total_eligible_students: 3,
    distinct_students_applied: 2,
    total_applications: 3,
    distinct_students_submitted: 2,
    distinct_students_shortlisted: 2,
    distinct_students_interviewed: 2,
    distinct_students_selected: 2,
    total_selections: 3,
    single_offer_students: 1,
    dual_offer_students: 1,
    multi_offer_students: 0,
    total_offers_issued: 3,
    total_offers_accepted: 1,
    total_offers_declined: 1,
    total_offers_pending: 1,
    distinct_students_joined: 1,
    distinct_students_not_joined: 0,
    distinct_students_pending_outcomes: 1,
    placement_rate_eligible: 66.67,
    placement_rate_applicants: 100.0,
    interview_selection_rate: 100.0,
    offer_acceptance_rate: 50.0,
    joining_rate: 100.0,
    overall_pipeline_yield: 33.33,
  },
  department_breakdown: [
    {
      department: 'Computer Science',
      total_students: 2,
      applied_students: 2,
      selected_students: 2,
      joined_students: 1,
      placement_rate: 100.0,
    },
    {
      department: 'Electronics',
      total_students: 1,
      applied_students: 0,
      selected_students: 0,
      joined_students: 0,
      placement_rate: 0.0,
    },
  ],
  metric_definitions: [
    {
      metric_name: 'Eligible Cohort Placement Rate',
      percentage: 66.67,
      numerator: 2,
      numerator_label: 'Distinct Students Selected',
      denominator: 3,
      denominator_label: 'Eligible Students in Cohort',
      formula: '(Distinct Students Selected / Verified Eligible Cohort) * 100',
      records_count: 3,
      notes: 'Measures institutional placement conversion without dual counting.',
    },
  ],
  generated_at: '2026-10-28T10:00:00Z',
};

const mockFeedbackData = {
  anonymity_rule_enforced: true,
  minimum_group_threshold: 3,
  kpi_summary: {
    total_recruiter_evaluations: 5,
    total_student_experiences: 6,
    total_trainer_assessments: 4,
    avg_recruiter_tech_rating: 4.2,
    avg_recruiter_comm_rating: 4.0,
    avg_recruiter_satisfaction: 4.5,
    avg_trainer_effectiveness: 4.6,
  },
  recruiter_ratings: {
    avg_technical: 4.2,
    avg_communication: 4.0,
    avg_satisfaction: 4.5,
    distribution_quality: { EXCELLENT: 3, GOOD: 2 },
  },
  student_difficulty_breakdown: [
    { difficulty: 'HARD', count: 4, percentage: 66.67 },
    { difficulty: 'MEDIUM', count: 2, percentage: 33.33 },
  ],
  trainer_readiness_breakdown: [
    { readiness: 'HIGHLY_READY', count: 3, percentage: 75.0 },
    { readiness: 'READY', count: 1, percentage: 25.0 },
  ],
  recruiter_remarks_sample: [
    {
      id: 'rem-1',
      company_name: 'Alpha Cloud Tech',
      role_title: 'Backend Software Engineer',
      category: 'TECHNICAL',
      remark: 'Strong Python foundation, needs polish on database indexing.',
      rating: 4,
      date: '2026-10-20',
    },
  ],
  student_suggestions_sample: [
    {
      id: 'sug-1',
      company_name: 'Alpha Cloud Tech',
      difficulty: 'HARD',
      suggestion: 'Emphasize database transactions and Redis caching in mock interviews.',
      interview_experience: 'Challenging live coding round.',
      date: '2026-10-21',
      is_anonymous: true,
    },
  ],
  trainer_improvement_areas_sample: [],
  generated_at: '2026-10-28T10:00:00Z',
};

const mockSkillGapData = {
  ai_disclaimer: 'Purely deterministic evidence-based calculation from actual test attempts and requirements.',
  total_market_demand_skills: 8,
  total_assessed_skills: 5,
  unassessed_high_demand_skills: 2,
  critical_gap_skills: 1,
  skill_matrix: [
    {
      skill: 'Python',
      jobs_requiring: 4,
      companies_requiring: 3,
      assessment_tests_count: 2,
      total_attempts: 15,
      passed_attempts: 13,
      pass_percentage: 86.67,
      student_skill_profiles_count: 20,
      mock_evaluations_count: 10,
      hr_feedback_count: 4,
      coverage_category: 'EVALUATED_WELL',
      recommendation: 'Strong candidate pool ready for corporate dispatch.',
    },
    {
      skill: 'Data Structures',
      jobs_requiring: 5,
      companies_requiring: 4,
      assessment_tests_count: 2,
      total_attempts: 20,
      passed_attempts: 9,
      pass_percentage: 45.0,
      student_skill_profiles_count: 18,
      mock_evaluations_count: 8,
      hr_feedback_count: 5,
      coverage_category: 'CRITICAL_GAP',
      recommendation: 'Pass rate below 60%. Remedial training and mock problem-solving drills recommended.',
    },
    {
      skill: 'AWS Cloud',
      jobs_requiring: 3,
      companies_requiring: 2,
      assessment_tests_count: 0,
      total_attempts: 0,
      passed_attempts: 0,
      pass_percentage: 0.0,
      student_skill_profiles_count: 2,
      mock_evaluations_count: 0,
      hr_feedback_count: 0,
      coverage_category: 'UNASSESSED_DEMAND',
      recommendation: 'High market demand but zero institutional assessments. Introduce diagnostic evaluation.',
    },
  ],
  generated_at: '2026-10-28T10:00:00Z',
};

const mockTrainingPlans = [
  {
    id: 'plan-001',
    title: 'Remedial Data Structures Acceleration Program',
    plan_code: 'TRP-2026-001',
    target_skill: 'Data Structures',
    evidence_rationale: 'Pass rate in internal DSA diagnostic test is 45.0%.',
    target_cohort_year: 2026,
    target_department: 'Computer Science',
    target_eligible_count: 45,
    enrolled_students_count: 0,
    proposed_objectives: 'Elevate cohort clearance to 80%+ on array, trees, and dynamic programming.',
    planned_activities: '10 weekend problem-solving labs with timed HackerRank drills.',
    responsible_trainer_name: 'Dr. Alan Turing',
    status: 'PROPOSED',
    approved_by_name: null,
    approved_at: null,
    approval_notes: '',
    actual_completion_results: '',
    created_by_name: 'Placement Officer',
    created_at: '2026-10-25T10:00:00Z',
    updated_at: '2026-10-25T10:00:00Z',
  },
];

const mockCycleReviews = [
  {
    id: 'cycle-001',
    cycle_name: 'Campus Recruitment 2026-27 Improvement Cycle',
    cycle_code: 'CYC-2026-001',
    academic_year: '2026-2027',
    status: 'ACTIVE',
    baseline_metrics_snapshot: {
      captured_placement_rate: 66.67,
      captured_eligible_count: 3,
      captured_selected_count: 2,
      snapshot_timestamp: '2026-10-28T09:00:00Z',
    },
    goals_and_targets: 'Achieve 85%+ cohort placement rate.',
    review_summary: 'Baseline initialized from previous drive outcomes.',
    lead_reviewer_name: 'Placement Head Officer',
    total_actions: 1,
    completed_actions: 0,
    action_items: [
      {
        id: 'act-001',
        cycle_review: 'cycle-001',
        title: 'Remedial DSA Weekend Intensive Drills',
        category: 'CURRICULUM_TRAINING',
        action_description: 'Launch weekend coding labs targeting critical DSA gap.',
        success_criteria: '80% clearance on post-training assessment test.',
        owner_name: 'Placement Head',
        status: 'PLANNED',
        outcome_notes: '',
        created_at: '2026-10-28T09:30:00Z',
        updated_at: '2026-10-28T09:30:00Z',
      },
    ],
    created_at: '2026-10-28T09:00:00Z',
    updated_at: '2026-10-28T09:00:00Z',
  },
];

const mockDiagnostics = {
  overall_health: 'HEALTHY',
  overall_score: 100,
  checks: [
    {
      code: 'CHK_ORPHAN_PLACEMENTS',
      name: 'Orphaned Placement Records',
      status: 'PASS',
      count: 0,
      message: 'Zero orphaned placement results detected.',
      impact: 'Authoritative reporting integrity guaranteed.',
      actionable_guidance: 'No action required.',
    },
    {
      code: 'CHK_UNASSESSED_DEMAND',
      name: 'Unassessed In-Demand Market Skills',
      status: 'WARNING',
      count: 1,
      message: '1 market skill required by companies has zero tests.',
      impact: 'Candidates submitted without validated skill proof.',
      actionable_guidance: 'Create assessment test in apps.preparation.',
    },
  ],
  timestamp: '2026-10-28T10:00:00Z',
};

describe('Phase 13: Continuous Improvement Hub Frontend', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (continuousImprovementApi.getPlacementRate as any).mockResolvedValue(mockPlacementData);
    (continuousImprovementApi.getFeedbackIntelligence as any).mockResolvedValue(mockFeedbackData);
    (continuousImprovementApi.getSkillGapMatrix as any).mockResolvedValue(mockSkillGapData);
    (continuousImprovementApi.getTrainingPlans as any).mockResolvedValue(mockTrainingPlans);
    (continuousImprovementApi.getCycleReviews as any).mockResolvedValue(mockCycleReviews);
    (continuousImprovementApi.getDiagnostics as any).mockResolvedValue(mockDiagnostics);
  });

  const renderComponent = () => {
    const queryClient = createTestQueryClient();
    return render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <MemoryRouter>
            <ContinuousImprovementHubPage />
          </MemoryRouter>
        </AuthProvider>
      </QueryClientProvider>
    );
  };

  it('1. Renders Hub Header with Phase 13 Brand Badges and Zero-AI Safeguard', async () => {
    renderComponent();
    expect(screen.getByText('Continuous Improvement Hub')).toBeInTheDocument();
    expect(screen.getByText('Phase 13: Continuous Improvement')).toBeInTheDocument();
    expect(screen.getByText('Deterministic / Zero AI')).toBeInTheDocument();
    expect(screen.getByText('Placement Head Gate')).toBeInTheDocument();
  });

  it('2. Renders Tab 1 Placement Rate Analytics with explicit formulas & distinct candidate funnel', async () => {
    renderComponent();
    await waitFor(() => {
      expect(screen.getAllByText('66.67%').length).toBeGreaterThan(0);
    });
    expect(screen.getByText('Eligible Placement Rate')).toBeInTheDocument();
    expect(screen.getByText('Applicant Conversion')).toBeInTheDocument();
    expect(screen.getByText('Distinct Student Conversion Funnel')).toBeInTheDocument();
    expect(screen.getByText('Department-wise Placement Performance')).toBeInTheDocument();
    expect(screen.getByText('Metric Proofs, Denominators & Traceability Standards')).toBeInTheDocument();
  });

  it('3. Switches to Tab 2 Feedback Intelligence and displays anonymity warning and recruiter ratings', async () => {
    renderComponent();
    const feedbackTab = screen.getByText('2. Feedback Intelligence');
    fireEvent.click(feedbackTab);

    await waitFor(() => {
      expect(screen.getByText(/Institutional Privacy & Safe Anonymity Guarantee/i)).toBeInTheDocument();
      expect(screen.getByText('4.2 / 5.0')).toBeInTheDocument();
      expect(screen.getByText('Student Interview Difficulty Perception')).toBeInTheDocument();
    });
  });

  it('4. Switches to Tab 3 Skill Gap Matrix and renders evidence coverage badges', async () => {
    renderComponent();
    const skillsTab = screen.getByText('3. Skill Gap Matrix');
    fireEvent.click(skillsTab);

    await waitFor(() => {
      expect(screen.getByText('Skill Demand vs Assessment Performance Matrix')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('Evaluated & Strong')).toBeInTheDocument();
      expect(screen.getByText('Critical Weakness (<60% Pass)')).toBeInTheDocument();
      expect(screen.getByText('Unassessed Market Demand')).toBeInTheDocument();
    });
  });

  it('5. Switches to Tab 4 Training Plans and displays proposed plan cards', async () => {
    renderComponent();
    const trainingTab = screen.getByText('4. Training Plans');
    fireEvent.click(trainingTab);

    await waitFor(() => {
      expect(screen.getByText('Remedial Data Structures Acceleration Program')).toBeInTheDocument();
      expect(screen.getByText('TRP-2026-001')).toBeInTheDocument();
      expect(screen.getByText('PROPOSED')).toBeInTheDocument();
    });
  });

  it('6. Switches to Tab 5 Recruitment Cycle Improvement and displays baseline snapshots & action items', async () => {
    renderComponent();
    const cycleTab = screen.getByText('5. Cycle Improvement');
    fireEvent.click(cycleTab);

    await waitFor(() => {
      expect(screen.getByText('Campus Recruitment 2026-27 Improvement Cycle')).toBeInTheDocument();
      expect(screen.getByText('Cycle Baseline Metrics Snapshot (Frozen Provenance)')).toBeInTheDocument();
      expect(screen.getByText('Remedial DSA Weekend Intensive Drills')).toBeInTheDocument();
    });
  });

  it('7. Switches to Tab 6 Diagnostics and displays 6-point integrity audit grid', async () => {
    renderComponent();
    const diagTab = screen.getByText('6. Diagnostics');
    fireEvent.click(diagTab);

    await waitFor(() => {
      expect(screen.getByText('Continuous Improvement Data Quality Score')).toBeInTheDocument();
      expect(screen.getByText('Orphaned Placement Records')).toBeInTheDocument();
      expect(screen.getByText('Unassessed In-Demand Market Skills')).toBeInTheDocument();
    });
  });

  it('8. Triggers CSV export when clicking Export CSV in placement tab', async () => {
    (continuousImprovementApi.exportPlacementRateCsv as any).mockResolvedValue(new Blob(['test']));
    renderComponent();

    const exportBtn = screen.getByText('Export CSV');
    expect(exportBtn).toBeInTheDocument();
    const placementCsvItem = screen.getByText('Placement Rates CSV');
    fireEvent.click(placementCsvItem);

    await waitFor(() => {
      expect(continuousImprovementApi.exportPlacementRateCsv).toHaveBeenCalled();
    });
  });
});
