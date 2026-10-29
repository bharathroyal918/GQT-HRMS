import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  TrendingUp,
  BarChart3,
  BrainCircuit,
  GraduationCap,
  RotateCcw,
  ShieldAlert,
  Download,
  Filter,
  CheckCircle2,
  Clock,
  Award,
  Users,
  Info,
  Briefcase,
  Layers,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import {
  continuousImprovementApi,
  downloadCsvBlob,
} from '../../api/continuousImprovementApi';
import {
  PlacementRateFilter,
  TrainingPlan,
  TrainingPlanStatus,
  SkillCoverageCategory,
  TrainingPlanCreatePayload,
} from '../../types/continuousImprovement';

type ActiveTab =
  | 'placement'
  | 'feedback'
  | 'skills'
  | 'training'
  | 'cycles'
  | 'diagnostics';

export const ContinuousImprovementHubPage: React.FC = () => {
  const { hasAnyRole } = useAuth();
  const queryClient = useQueryClient();

  const isPlacementHead = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD']);

  // UI state
  const [activeTab, setActiveTab] = useState<ActiveTab>('placement');
  const [filters, setFilters] = useState<PlacementRateFilter>({
    cohort_year: 2026,
    department: '',
  });

  // Modal states
  const [isNewPlanModalOpen, setIsNewPlanModalOpen] = useState(false);
  const [transitionPlan, setTransitionPlan] = useState<{
    plan: TrainingPlan;
    targetStatus: TrainingPlanStatus;
  } | null>(null);
  const [transitionNotes, setTransitionNotes] = useState('');
  const [newPlanForm, setNewPlanForm] = useState<TrainingPlanCreatePayload>({
    title: '',
    target_skill: '',
    evidence_rationale: '',
    target_cohort_year: 2026,
    target_department: '',
    proposed_objectives: '',
    planned_activities: '',
    expected_outcome: '',
  });

  // Cycle Modal state
  const [isNewCycleModalOpen, setIsNewCycleModalOpen] = useState(false);
  const [newCycleForm, setNewCycleForm] = useState({
    cycle_name: 'Campus Recruitment 2026-27 Improvement Cycle',
    academic_year: '2026-2027',
    goals_and_targets: 'Achieve 85%+ cohort placement rate and eliminate unassessed demand in DSA and Cloud.',
    review_summary: 'Baseline initialized from previous drive outcomes.',
  });

  const [newActionCycleId, setNewActionCycleId] = useState<string | null>(null);
  const [newActionForm, setNewActionForm] = useState({
    title: '',
    category: 'CURRICULUM_TRAINING' as const,
    action_description: '',
    success_criteria: '',
    due_date: '',
  });

  // -------------------------------------------------------------------------
  // Data Queries
  // -------------------------------------------------------------------------
  const placementQuery = useQuery({
    queryKey: ['placement-rate', filters],
    queryFn: () => continuousImprovementApi.getPlacementRate(filters),
  });

  const feedbackQuery = useQuery({
    queryKey: ['feedback-intelligence', filters.cohort_year],
    queryFn: () =>
      continuousImprovementApi.getFeedbackIntelligence({
        cohort_year: filters.cohort_year,
      }),
  });

  const skillGapQuery = useQuery({
    queryKey: ['skill-gap-matrix', filters.cohort_year],
    queryFn: () =>
      continuousImprovementApi.getSkillGapMatrix({
        cohort_year: filters.cohort_year,
      }),
  });

  const trainingPlansQuery = useQuery({
    queryKey: ['training-plans'],
    queryFn: () => continuousImprovementApi.getTrainingPlans(),
  });

  const cycleReviewsQuery = useQuery({
    queryKey: ['recruitment-cycles'],
    queryFn: () => continuousImprovementApi.getCycleReviews(),
  });

  const diagnosticsQuery = useQuery({
    queryKey: ['improvement-diagnostics'],
    queryFn: () => continuousImprovementApi.getDiagnostics(),
  });

  // -------------------------------------------------------------------------
  // Mutations
  // -------------------------------------------------------------------------
  const createPlanMutation = useMutation({
    mutationFn: (payload: TrainingPlanCreatePayload) =>
      continuousImprovementApi.createTrainingPlan(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-plans'] });
      setIsNewPlanModalOpen(false);
      setNewPlanForm({
        title: '',
        target_skill: '',
        evidence_rationale: '',
        target_cohort_year: 2026,
        target_department: '',
        proposed_objectives: '',
        planned_activities: '',
        expected_outcome: '',
      });
    },
  });

  const transitionPlanMutation = useMutation({
    mutationFn: ({
      planId,
      status,
      notes,
    }: {
      planId: string;
      status: TrainingPlanStatus;
      notes: string;
    }) =>
      continuousImprovementApi.transitionTrainingPlan(planId, {
        status,
        approval_notes: status === 'APPROVED' ? notes : undefined,
        actual_completion_results: status === 'COMPLETED' ? notes : undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['training-plans'] });
      setTransitionPlan(null);
      setTransitionNotes('');
    },
  });

  const createCycleMutation = useMutation({
    mutationFn: () =>
      continuousImprovementApi.createCycleReview({
        ...newCycleForm,
        capture_current_baseline: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-cycles'] });
      setIsNewCycleModalOpen(false);
    },
  });

  const createActionMutation = useMutation({
    mutationFn: (cycleId: string) =>
      continuousImprovementApi.createCycleAction({
        cycle_review_id: cycleId,
        ...newActionForm,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-cycles'] });
      setNewActionCycleId(null);
      setNewActionForm({
        title: '',
        category: 'CURRICULUM_TRAINING',
        action_description: '',
        success_criteria: '',
        due_date: '',
      });
    },
  });

  const updateActionStatusMutation = useMutation({
    mutationFn: ({
      actionId,
      status,
    }: {
      actionId: string;
      status: string;
    }) => continuousImprovementApi.updateCycleActionStatus(actionId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recruitment-cycles'] });
    },
  });

  // Export CSV Handlers
  const handleExportPlacementCsv = async () => {
    const blob = await continuousImprovementApi.exportPlacementRateCsv(filters);
    downloadCsvBlob(blob, `GQT_Placement_Rate_Report_${filters.cohort_year || 'all'}.csv`);
  };

  const handleExportSkillGapCsv = async () => {
    const blob = await continuousImprovementApi.exportSkillGapCsv({
      cohort_year: filters.cohort_year,
    });
    downloadCsvBlob(blob, `GQT_Skill_Gap_Matrix_${filters.cohort_year || 'all'}.csv`);
  };

  const handleExportTrainingPlansCsv = async () => {
    const blob = await continuousImprovementApi.exportTrainingPlansCsv();
    downloadCsvBlob(blob, `GQT_Continuous_Training_Plans.csv`);
  };

  // Helper for status badge styling
  const getStatusBadge = (status: TrainingPlanStatus) => {
    switch (status) {
      case 'DRAFT':
        return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'PROPOSED':
        return 'bg-amber-50 text-amber-700 border-amber-300';
      case 'APPROVED':
        return 'bg-blue-50 text-blue-700 border-blue-300';
      case 'SCHEDULED':
        return 'bg-purple-50 text-purple-700 border-purple-300';
      case 'IN_PROGRESS':
        return 'bg-indigo-50 text-indigo-700 border-indigo-300';
      case 'COMPLETED':
        return 'bg-emerald-50 text-emerald-700 border-emerald-300';
      case 'CANCELLED':
        return 'bg-rose-50 text-rose-700 border-rose-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const getCoverageBadge = (cat: SkillCoverageCategory) => {
    switch (cat) {
      case 'EVALUATED_WELL':
      case 'STRENGTH':
        return {
          label: 'Evaluated & Strong',
          className: 'bg-emerald-100 text-emerald-800 border-emerald-200',
        };
      case 'CRITICAL_GAP':
        return {
          label: 'Critical Weakness (<60% Pass)',
          className: 'bg-rose-100 text-rose-800 border-rose-200',
        };
      case 'UNASSESSED_DEMAND':
        return {
          label: 'Unassessed Market Demand',
          className: 'bg-amber-100 text-amber-800 border-amber-200',
        };
      case 'MODERATE_GAP':
        return {
          label: 'Moderate Gap (60–74% Pass)',
          className: 'bg-amber-100 text-amber-800 border-amber-200',
        };
      case 'SUFFICIENT_EVIDENCE':
        return {
          label: 'Sufficient Evidence',
          className: 'bg-blue-100 text-blue-800 border-blue-200',
        };
      case 'MONITORING':
      default:
        return {
          label: 'Monitoring Required',
          className: 'bg-slate-100 text-slate-800 border-slate-200',
        };
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* ------------------------------------------------------------------- */}
      {/* 1. Brand Header */}
      {/* ------------------------------------------------------------------- */}
      <div className="bg-gradient-to-r from-gqt-navy via-gqt-navy-dark to-[#0A2558] text-white p-6 sm:p-8 rounded-2xl shadow-xl border border-white/10 relative overflow-hidden">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-80 h-80 bg-gqt-blue/15 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-gqt-blue/30 text-blue-200 border border-blue-400/30">
                Phase 13: Continuous Improvement
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-400/30">
                Deterministic / Zero AI
              </span>
              <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-purple-500/20 text-purple-200 border border-purple-400/30">
                Placement Head Gate
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Continuous Improvement Hub
            </h1>
            <p className="text-sm sm:text-base text-gray-300 mt-1 max-w-3xl">
              Transform recruitment records, student feedback, and evaluation matrices into an
              auditable, evidence-based improvement loop across training and placement cycles.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => {
                queryClient.invalidateQueries();
              }}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg text-sm font-semibold border border-white/20 transition-colors flex items-center gap-2"
              title="Refresh Analytics Dataset"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
            <div className="relative group">
              <button
                className="px-4 py-2 bg-gqt-blue hover:bg-blue-600 text-white rounded-lg text-sm font-semibold shadow-md transition-all flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </button>
              <div className="absolute right-0 mt-1 w-56 bg-white rounded-xl shadow-2xl border border-gray-100 hidden group-hover:block z-50 py-1 text-gray-800 text-sm">
                <button
                  onClick={handleExportPlacementCsv}
                  className="w-full text-left px-4 py-2.5 hover:bg-gray-50 flex items-center gap-2 text-xs font-medium"
                >
                  <TrendingUp className="w-3.5 h-3.5 text-gqt-blue" />
                  Placement Rates CSV
                </button>
                <button
                  onClick={handleExportSkillGapCsv}
                  className="w-full text-left px-4 py-2.5 hover:bg-gray-50 flex items-center gap-2 text-xs font-medium"
                >
                  <BrainCircuit className="w-3.5 h-3.5 text-indigo-600" />
                  Skill Gap Matrix CSV
                </button>
                <button
                  onClick={handleExportTrainingPlansCsv}
                  className="w-full text-left px-4 py-2.5 hover:bg-gray-50 flex items-center gap-2 text-xs font-medium"
                >
                  <GraduationCap className="w-3.5 h-3.5 text-emerald-600" />
                  Training Plans CSV
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 2. Global Filter Bar */}
      {/* ------------------------------------------------------------------- */}
      <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-600">
            <Filter className="w-4 h-4 text-gqt-navy" />
            <span>Filter Cohort:</span>
          </div>

          <select
            value={filters.cohort_year || ''}
            onChange={(e) =>
              setFilters({
                ...filters,
                cohort_year: e.target.value ? parseInt(e.target.value) : undefined,
              })
            }
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
          >
            <option value="2026">Cohort 2026</option>
            <option value="2025">Cohort 2025</option>
            <option value="2024">Cohort 2024</option>
            <option value="">All Cohorts</option>
          </select>

          <select
            value={filters.department || ''}
            onChange={(e) => setFilters({ ...filters, department: e.target.value })}
            className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
          >
            <option value="">All Departments</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Information Science">Information Science</option>
            <option value="Electronics">Electronics & Communication</option>
            <option value="Mechanical">Mechanical</option>
          </select>

          {(filters.cohort_year !== 2026 || filters.department) && (
            <button
              onClick={() => setFilters({ cohort_year: 2026, department: '' })}
              className="text-xs text-gqt-blue hover:underline font-semibold"
            >
              Reset Filters
            </button>
          )}
        </div>

        <div className="text-xs text-gray-500 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          <span>Real-time authoritative sync from institutional records</span>
        </div>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* 3. Navigation Tabs */}
      {/* ------------------------------------------------------------------- */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-1 sm:space-x-4 overflow-x-auto" aria-label="Tabs">
          {[
            { id: 'placement', name: '1. Placement Rates', icon: TrendingUp },
            { id: 'feedback', name: '2. Feedback Intelligence', icon: BarChart3 },
            { id: 'skills', name: '3. Skill Gap Matrix', icon: BrainCircuit },
            { id: 'training', name: '4. Training Plans', icon: GraduationCap },
            { id: 'cycles', name: '5. Cycle Improvement', icon: RotateCcw },
            { id: 'diagnostics', name: '6. Diagnostics', icon: ShieldAlert },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as ActiveTab)}
                className={`py-3 px-4 inline-flex items-center gap-2 border-b-2 font-semibold text-sm whitespace-nowrap transition-colors ${
                  isActive
                    ? 'border-gqt-blue text-gqt-blue bg-blue-50/50 rounded-t-lg'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-gqt-blue' : 'text-gray-400'}`} />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* ------------------------------------------------------------------- */}
      {/* TAB 1: Granular Placement Rate Analytics */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'placement' && (
        <div className="space-y-6">
          {placementQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Calculating placement rates...</div>
          ) : placementQuery.isError ? (
            <div className="p-6 bg-rose-50 text-rose-700 rounded-xl border border-rose-200">
              Error fetching placement analytics. Verify user permissions.
            </div>
          ) : (
            <>
              {/* Primary KPI Summary Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Eligible Placement Rate
                    </span>
                    <span className="p-2 bg-blue-50 text-gqt-blue rounded-lg">
                      <Award className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-gqt-navy">
                      {placementQuery.data?.summary.placement_rate_eligible}%
                    </span>
                    <span className="text-xs text-gray-500">
                      ({placementQuery.data?.summary.distinct_students_selected} of{' '}
                      {placementQuery.data?.summary.total_eligible_students} eligible)
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Distinct verified candidates with ≥1 confirmed job selection.
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Applicant Conversion
                    </span>
                    <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                      <Users className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-emerald-700">
                      {placementQuery.data?.summary.placement_rate_applicants}%
                    </span>
                    <span className="text-xs text-gray-500">
                      ({placementQuery.data?.summary.distinct_students_selected} of{' '}
                      {placementQuery.data?.summary.distinct_students_applied} applied)
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Selection yield among actively registered applicants.
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Offer Acceptance Rate
                    </span>
                    <span className="p-2 bg-purple-50 text-purple-600 rounded-lg">
                      <CheckCircle2 className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-purple-700">
                      {placementQuery.data?.summary.offer_acceptance_rate}%
                    </span>
                    <span className="text-xs text-gray-500">
                      ({placementQuery.data?.summary.total_offers_accepted} accepted)
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Resolved offers accepted ({placementQuery.data?.summary.total_offers_declined} declined).
                  </p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                      Confirmed Joining Rate
                    </span>
                    <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
                      <Briefcase className="w-5 h-5" />
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-amber-700">
                      {placementQuery.data?.summary.joining_rate}%
                    </span>
                    <span className="text-xs text-gray-500">
                      ({placementQuery.data?.summary.distinct_students_joined} joined)
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Conversion of offer acceptors to official on-site joiners.
                  </p>
                </div>
              </div>

              {/* Distinct Student Recruitment Funnel */}
              <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                <h3 className="text-base font-bold text-gqt-navy mb-4 flex items-center gap-2">
                  <Layers className="w-5 h-5 text-gqt-blue" />
                  Distinct Student Conversion Funnel
                </h3>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-center">
                  <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="text-xs text-gray-500">1. Total Cohort</div>
                    <div className="text-xl font-bold text-gqt-navy mt-1">
                      {placementQuery.data?.summary.total_cohort_students}
                    </div>
                    <div className="text-[11px] text-gray-400 mt-0.5">Enrolled</div>
                  </div>

                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="text-xs text-blue-700 font-semibold">2. Eligible</div>
                    <div className="text-xl font-bold text-blue-900 mt-1">
                      {placementQuery.data?.summary.total_eligible_students}
                    </div>
                    <div className="text-[11px] text-blue-600 mt-0.5">Verified</div>
                  </div>

                  <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                    <div className="text-xs text-indigo-700 font-semibold">3. Applied</div>
                    <div className="text-xl font-bold text-indigo-900 mt-1">
                      {placementQuery.data?.summary.distinct_students_applied}
                    </div>
                    <div className="text-[11px] text-indigo-600 mt-0.5">
                      ({placementQuery.data?.summary.total_applications} apps)
                    </div>
                  </div>

                  <div className="p-3 bg-cyan-50 rounded-lg border border-cyan-200">
                    <div className="text-xs text-cyan-700 font-semibold">4. Interviewed</div>
                    <div className="text-xl font-bold text-cyan-900 mt-1">
                      {placementQuery.data?.summary.distinct_students_interviewed}
                    </div>
                    <div className="text-[11px] text-cyan-600 mt-0.5">Attended</div>
                  </div>

                  <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                    <div className="text-xs text-emerald-700 font-semibold">5. Selected</div>
                    <div className="text-xl font-bold text-emerald-900 mt-1">
                      {placementQuery.data?.summary.distinct_students_selected}
                    </div>
                    <div className="text-[11px] text-emerald-600 mt-0.5">
                      ({placementQuery.data?.summary.total_selections} offers)
                    </div>
                  </div>

                  <div className="p-3 bg-teal-50 rounded-lg border border-teal-200">
                    <div className="text-xs text-teal-700 font-semibold">6. Joined</div>
                    <div className="text-xl font-bold text-teal-900 mt-1">
                      {placementQuery.data?.summary.distinct_students_joined}
                    </div>
                    <div className="text-[11px] text-teal-600 mt-0.5">Confirmed</div>
                  </div>
                </div>

                {/* Multi-Offer distribution */}
                <div className="mt-4 pt-4 border-t border-gray-100 flex flex-wrap items-center justify-between text-xs text-gray-600 gap-4">
                  <div className="flex items-center gap-4">
                    <span className="font-semibold text-gray-700">Multi-Offer Distribution:</span>
                    <span>Single Offer: <b>{placementQuery.data?.summary.single_offer_students}</b></span>
                    <span>Dual Offers: <b>{placementQuery.data?.summary.dual_offer_students}</b></span>
                    <span>3+ Offers: <b>{placementQuery.data?.summary.multi_offer_students}</b></span>
                  </div>
                  <div className="text-gray-500">
                    Pending Outcomes: <b>{placementQuery.data?.summary.distinct_students_pending_outcomes}</b> candidate(s)
                  </div>
                </div>
              </div>

              {/* Department Breakdown Table */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-gqt-navy">
                    Department-wise Placement Performance
                  </h3>
                  <span className="text-xs text-gray-500">
                    Cohort {filters.cohort_year || 'Consolidated'}
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3">Department</th>
                        <th className="px-6 py-3 text-right">Total Students</th>
                        <th className="px-6 py-3 text-right">Applied</th>
                        <th className="px-6 py-3 text-right">Selected</th>
                        <th className="px-6 py-3 text-right">Joined</th>
                        <th className="px-6 py-3 text-right">Placement Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {placementQuery.data?.department_breakdown.map((dept) => (
                        <tr key={dept.department} className="hover:bg-gray-50/80 transition-colors">
                          <td className="px-6 py-3.5 font-medium text-gqt-navy">
                            {dept.department}
                          </td>
                          <td className="px-6 py-3.5 text-right text-gray-600">{dept.total_students}</td>
                          <td className="px-6 py-3.5 text-right text-gray-600">{dept.applied_students}</td>
                          <td className="px-6 py-3.5 text-right font-semibold text-emerald-600">
                            {dept.selected_students}
                          </td>
                          <td className="px-6 py-3.5 text-right text-gray-700">{dept.joined_students}</td>
                          <td className="px-6 py-3.5 text-right">
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-blue-50 text-gqt-blue border border-blue-200">
                              {dept.placement_rate}%
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Mathematical Proof & Formulas Disclosure */}
              <div className="bg-gray-50 p-6 rounded-xl border border-gray-200">
                <h4 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3 flex items-center gap-1.5">
                  <Info className="w-4 h-4 text-gqt-blue" />
                  Metric Proofs, Denominators & Traceability Standards
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {placementQuery.data?.metric_definitions.map((def) => (
                    <div
                      key={def.metric_name}
                      className="bg-white p-3.5 rounded-lg border border-gray-200 text-xs space-y-1"
                    >
                      <div className="flex justify-between items-center font-bold text-gray-800">
                        <span>{def.metric_name}</span>
                        <span className="text-gqt-blue">{def.percentage}%</span>
                      </div>
                      <div className="text-gray-500">
                        Formula: <code className="bg-gray-100 px-1 py-0.5 rounded">{def.formula}</code>
                      </div>
                      <div className="text-gray-600">
                        Numerator: <b>{def.numerator}</b> ({def.numerator_label}) / Denominator:{' '}
                        <b>{def.denominator}</b> ({def.denominator_label})
                      </div>
                      <div className="text-gray-400 text-[11px] pt-1">{def.notes}</div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* TAB 2: Feedback Intelligence */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'feedback' && (
        <div className="space-y-6">
          {feedbackQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Aggregating cross-category feedback...</div>
          ) : feedbackQuery.isError ? (
            <div className="p-6 bg-rose-50 text-rose-700 rounded-xl border border-rose-200">
              Error loading feedback intelligence.
            </div>
          ) : (
            <>
              {/* Anonymity Banner */}
              <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-800">
                  <span className="font-bold">Institutional Privacy & Safe Anonymity Guarantee: </span>
                  Candidate feedback is aggregated under an enforced minimum-group policy (≥3 responses).
                  Direct candidate identities are stripped from student evaluation exports. All free-text
                  remarks are untrusted inputs treated purely as informative feedback.
                </div>
              </div>

              {/* Feedback KPI Summary */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Recruiter Tech Rating
                  </span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-gqt-navy">
                      {feedbackQuery.data?.kpi_summary.avg_recruiter_tech_rating} / 5.0
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Technical skill competence rating</p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Recruiter Comm Rating
                  </span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-gqt-blue">
                      {feedbackQuery.data?.kpi_summary.avg_recruiter_comm_rating} / 5.0
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Professional communication evaluation</p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Recruiter Satisfaction
                  </span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-emerald-700">
                      {feedbackQuery.data?.kpi_summary.avg_recruiter_satisfaction} / 5.0
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Overall drive hiring experience</p>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                    Trainer Effectiveness
                  </span>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-3xl font-extrabold text-purple-700">
                      {feedbackQuery.data?.kpi_summary.avg_trainer_effectiveness} / 5.0
                    </span>
                  </div>
                  <p className="text-xs text-gray-400 mt-1">Pre-drive preparation rating</p>
                </div>
              </div>

              {/* Student Experience & Difficulty Breakdown */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <h4 className="text-sm font-bold text-gqt-navy mb-3">
                    Student Interview Difficulty Perception
                  </h4>
                  <div className="space-y-3">
                    {feedbackQuery.data?.student_difficulty_breakdown.map((item) => (
                      <div key={item.difficulty}>
                        <div className="flex justify-between text-xs font-medium text-gray-600 mb-1">
                          <span>{item.difficulty}</span>
                          <span>
                            {item.count} responses ({item.percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full ${
                              item.difficulty === 'HARD'
                                ? 'bg-rose-500'
                                : item.difficulty === 'MEDIUM'
                                ? 'bg-amber-500'
                                : 'bg-emerald-500'
                            }`}
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <h4 className="text-sm font-bold text-gqt-navy mb-3">
                    Trainer Readiness Certification Distribution
                  </h4>
                  <div className="space-y-3">
                    {feedbackQuery.data?.trainer_readiness_breakdown.map((item) => (
                      <div key={item.readiness}>
                        <div className="flex justify-between text-xs font-medium text-gray-600 mb-1">
                          <span>{item.readiness.replace('_', ' ')}</span>
                          <span>
                            {item.count} candidates ({item.percentage}%)
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2">
                          <div
                            className="h-2 rounded-full bg-gqt-blue"
                            style={{ width: `${item.percentage}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recruiter Remarks & Student Suggestions Samples */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <h4 className="text-sm font-bold text-gqt-navy mb-3">
                    Recruiter Qualitative Remarks (Industry Feedback)
                  </h4>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {feedbackQuery.data?.recruiter_remarks_sample.map((rem) => (
                      <div
                        key={rem.id}
                        className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs space-y-1"
                      >
                        <div className="flex justify-between text-gray-500">
                          <span className="font-semibold text-gqt-navy">{rem.company_name}</span>
                          <span>{rem.date}</span>
                        </div>
                        <p className="text-gray-700 italic">"{rem.remark}"</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm">
                  <h4 className="text-sm font-bold text-gqt-navy mb-3">
                    Student Suggestions & Interview Experiences (Anonymized)
                  </h4>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {feedbackQuery.data?.student_suggestions_sample.map((sug) => (
                      <div
                        key={sug.id}
                        className="p-3 bg-gray-50 rounded-lg border border-gray-200 text-xs space-y-1"
                      >
                        <div className="flex justify-between text-gray-500">
                          <span className="font-semibold text-gqt-navy">
                            {sug.company_name} ({sug.difficulty})
                          </span>
                          <span>{sug.date}</span>
                        </div>
                        <p className="text-gray-700 italic">"{sug.suggestion}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* TAB 3: Evidence-Based Skill Gap Matrix */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'skills' && (
        <div className="space-y-6">
          {skillGapQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Analyzing skill evidence matrix...</div>
          ) : skillGapQuery.isError ? (
            <div className="p-6 bg-rose-50 text-rose-700 rounded-xl border border-rose-200">
              Error fetching skill gap matrix.
            </div>
          ) : (
            <>
              {/* Methodology Notice */}
              <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex items-start gap-3">
                <Info className="w-5 h-5 text-gqt-blue shrink-0 mt-0.5" />
                <div className="text-xs text-blue-900">
                  <span className="font-bold">100% Deterministic Evidence-Based Scoring: </span>
                  {skillGapQuery.data?.ai_disclaimer} Unassessed skills are explicitly distinguished from
                  failed skills to prevent ungrounded inferences.
                </div>
              </div>

              {/* Counters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="bg-white p-4 rounded-xl border border-gray-200">
                  <span className="text-xs font-semibold text-gray-500">Total In-Demand Skills</span>
                  <div className="text-2xl font-extrabold text-gqt-navy mt-1">
                    {skillGapQuery.data?.total_market_demand_skills}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200">
                  <span className="text-xs font-semibold text-gray-500">Assessed by Institution</span>
                  <div className="text-2xl font-extrabold text-gqt-blue mt-1">
                    {skillGapQuery.data?.total_assessed_skills}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200">
                  <span className="text-xs font-semibold text-amber-700">Unassessed Demand</span>
                  <div className="text-2xl font-extrabold text-amber-600 mt-1">
                    {skillGapQuery.data?.unassessed_high_demand_skills}
                  </div>
                </div>
                <div className="bg-white p-4 rounded-xl border border-gray-200">
                  <span className="text-xs font-semibold text-rose-700">Critical Skill Gaps</span>
                  <div className="text-2xl font-extrabold text-rose-600 mt-1">
                    {skillGapQuery.data?.critical_gap_skills}
                  </div>
                </div>
              </div>

              {/* Skill Matrix Table */}
              <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                  <h3 className="text-sm font-bold text-gqt-navy">
                    Skill Demand vs Assessment Performance Matrix
                  </h3>
                  <button
                    onClick={handleExportSkillGapCsv}
                    className="text-xs text-gqt-blue hover:underline font-semibold flex items-center gap-1"
                  >
                    <Download className="w-3.5 h-3.5" /> Export Matrix CSV
                  </button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-50 text-gray-600 text-xs uppercase font-semibold border-b border-gray-200">
                      <tr>
                        <th className="px-6 py-3">Skill Track</th>
                        <th className="px-6 py-3 text-center">Job Demand</th>
                        <th className="px-6 py-3 text-center">Assessment Pass %</th>
                        <th className="px-6 py-3">Coverage Status</th>
                        <th className="px-6 py-3">Remedial Recommendation</th>
                        <th className="px-6 py-3 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {skillGapQuery.data?.skill_matrix.map((item) => {
                        const badge = getCoverageBadge(item.coverage_category);
                        return (
                          <tr key={item.skill} className="hover:bg-gray-50/80 transition-colors">
                            <td className="px-6 py-4 font-bold text-gqt-navy">{item.skill}</td>
                            <td className="px-6 py-4 text-center">
                              <span className="inline-block px-2 py-0.5 rounded text-xs font-semibold bg-gray-100 text-gray-700">
                                {item.jobs_requiring} jobs ({item.companies_requiring} cos)
                              </span>
                            </td>
                            <td className="px-6 py-4 text-center">
                              {item.total_attempts > 0 ? (
                                <span
                                  className={`font-extrabold ${
                                    item.pass_percentage >= 60
                                      ? 'text-emerald-600'
                                      : 'text-rose-600'
                                  }`}
                                >
                                  {item.pass_percentage}%{' '}
                                  <span className="text-xs font-normal text-gray-400">
                                    ({item.passed_attempts}/{item.total_attempts})
                                  </span>
                                </span>
                              ) : (
                                <span className="text-xs text-gray-400 italic">No tests recorded</span>
                              )}
                            </td>
                            <td className="px-6 py-4">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${badge.className}`}
                              >
                                {badge.label}
                              </span>
                            </td>
                            <td className="px-6 py-4 text-xs text-gray-600 max-w-xs">
                              {item.recommendation}
                            </td>
                            <td className="px-6 py-4 text-right">
                              {isPlacementHead && (
                                <button
                                  onClick={() => {
                                    setNewPlanForm({
                                      ...newPlanForm,
                                      title: `Remedial Training: ${item.skill} Acceleration`,
                                      target_skill: item.skill,
                                      evidence_rationale: item.recommendation,
                                      proposed_objectives: `Elevate cohort competence in ${item.skill} through targeted sessions and diagnostic tests.`,
                                    });
                                    setIsNewPlanModalOpen(true);
                                  }}
                                  className="text-xs bg-gqt-blue/10 hover:bg-gqt-blue hover:text-white text-gqt-blue font-semibold px-2.5 py-1.5 rounded transition-colors"
                                >
                                  Draft Plan
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* TAB 4: Remedial & Strategic Training Plans */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'training' && (
        <div className="space-y-6">
          {/* Header Action */}
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gqt-navy">Strategic Remedial Training Plans</h3>
              <p className="text-xs text-gray-500">
                Placement Head authorization gate enforced. Interventions cannot alter placement readiness automatically.
              </p>
            </div>
            {isPlacementHead && (
              <button
                onClick={() => setIsNewPlanModalOpen(true)}
                className="px-4 py-2 bg-gqt-navy hover:bg-gqt-navy-dark text-white rounded-lg text-sm font-semibold shadow-sm transition-all flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Draft New Training Plan
              </button>
            )}
          </div>

          {trainingPlansQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Loading training plans...</div>
          ) : trainingPlansQuery.isError ? (
            <div className="p-6 bg-rose-50 text-rose-700 rounded-xl border border-rose-200">
              Error loading training plans. Verify permissions.
            </div>
          ) : !trainingPlansQuery.data || !Array.isArray(trainingPlansQuery.data.training_plans) ? (
            <div className="p-6 bg-amber-50 text-amber-800 rounded-xl border border-amber-200">
              Unexpected response format from training plans service.
            </div>
          ) : trainingPlansQuery.data.training_plans.length === 0 ? (
            <div className="bg-white p-12 text-center rounded-xl border border-gray-200">
              <GraduationCap className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <h4 className="text-base font-bold text-gqt-navy">No Training Plans Initiated</h4>
              <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
                Draft a remediation plan based on identified skill gaps or recruiter feedback.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {trainingPlansQuery.data.summary && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <span className="text-xs font-semibold text-gray-500">Total Plans</span>
                    <div className="text-2xl font-extrabold text-gqt-navy mt-1">
                      {trainingPlansQuery.data.summary.total_plans}
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <span className="text-xs font-semibold text-amber-700">Proposed / Pending</span>
                    <div className="text-2xl font-extrabold text-amber-600 mt-1">
                      {trainingPlansQuery.data.summary.status_counts?.PROPOSED || 0}
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <span className="text-xs font-semibold text-gqt-blue">Approved & Active</span>
                    <div className="text-2xl font-extrabold text-gqt-blue mt-1">
                      {(trainingPlansQuery.data.summary.status_counts?.APPROVED || 0) +
                        (trainingPlansQuery.data.summary.status_counts?.IN_PROGRESS || 0) +
                        (trainingPlansQuery.data.summary.status_counts?.SCHEDULED || 0)}
                    </div>
                  </div>
                  <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
                    <span className="text-xs font-semibold text-emerald-700">Completed</span>
                    <div className="text-2xl font-extrabold text-emerald-600 mt-1">
                      {trainingPlansQuery.data.summary.status_counts?.COMPLETED || 0}
                    </div>
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {trainingPlansQuery.data.training_plans.map((plan) => (
                <div
                  key={plan.id}
                  className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[11px] font-mono text-gray-400">{plan.plan_code}</span>
                        <h4 className="text-base font-bold text-gqt-navy mt-0.5">{plan.title}</h4>
                      </div>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${getStatusBadge(
                          plan.status
                        )}`}
                      >
                        {plan.status}
                      </span>
                    </div>

                    <div className="mt-3 text-xs space-y-2 text-gray-600">
                      <div>
                        <span className="font-semibold text-gray-700">Target Skill:</span>{' '}
                        <span className="text-gqt-blue font-bold">{plan.target_skill}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-gray-700">Evidence Rationale:</span>{' '}
                        <span className="italic">{plan.evidence_rationale}</span>
                      </div>
                      <div>
                        <span className="font-semibold text-gray-700">Target Cohort:</span>{' '}
                        <span>
                          {plan.target_cohort_year || 'All'} ({plan.target_department || 'All Departments'})
                        </span>
                      </div>
                      {plan.responsible_trainer_name && (
                        <div>
                          <span className="font-semibold text-gray-700">Lead Trainer:</span>{' '}
                          <span>{plan.responsible_trainer_name}</span>
                        </div>
                      )}
                      {plan.approved_by_name && (
                        <div className="p-2 bg-blue-50/50 rounded border border-blue-100 text-[11px] text-blue-900">
                          Approved by <b>{plan.approved_by_name}</b> on{' '}
                          {plan.approved_at ? new Date(plan.approved_at).toLocaleDateString() : ''}
                          {plan.approval_notes && <p className="mt-0.5 italic">"{plan.approval_notes}"</p>}
                        </div>
                      )}
                      {plan.actual_completion_results && (
                        <div className="p-2 bg-emerald-50/50 rounded border border-emerald-100 text-[11px] text-emerald-900">
                          <b>Completion Results:</b> {plan.actual_completion_results}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Action transitions */}
                  <div className="mt-4 pt-3 border-t border-gray-100 flex flex-wrap items-center justify-end gap-2">
                    {plan.status === 'DRAFT' && isPlacementHead && (
                      <button
                        onClick={() =>
                          transitionPlanMutation.mutate({
                            planId: plan.id,
                            status: 'PROPOSED',
                            notes: '',
                          })
                        }
                        className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold rounded"
                      >
                        Submit Proposal
                      </button>
                    )}

                    {plan.status === 'PROPOSED' && isPlacementHead && (
                      <button
                        onClick={() =>
                          setTransitionPlan({ plan, targetStatus: 'APPROVED' })
                        }
                        className="px-3 py-1 bg-gqt-blue hover:bg-blue-600 text-white text-xs font-semibold rounded flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" /> Approve Plan
                      </button>
                    )}

                    {plan.status === 'APPROVED' && (
                      <button
                        onClick={() =>
                          transitionPlanMutation.mutate({
                            planId: plan.id,
                            status: 'IN_PROGRESS',
                            notes: '',
                          })
                        }
                        className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded"
                      >
                        Start Training
                      </button>
                    )}

                    {plan.status === 'IN_PROGRESS' && (
                      <button
                        onClick={() =>
                          setTransitionPlan({ plan, targetStatus: 'COMPLETED' })
                        }
                        className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded"
                      >
                        Mark Completed
                      </button>
                    )}
                  </div>
                </div>
              ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* TAB 5: Recruitment Cycle Improvement Reviews */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'cycles' && (
        <div className="space-y-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-gqt-navy">
                Recruitment Cycle Improvement Loop
              </h3>
              <p className="text-xs text-gray-500">
                Historical snapshot baselines, actionable commitments, and measurable cycle targets.
              </p>
            </div>
            {isPlacementHead && (
              <button
                onClick={() => setIsNewCycleModalOpen(true)}
                className="px-4 py-2 bg-gqt-navy hover:bg-gqt-navy-dark text-white rounded-lg text-sm font-semibold shadow-sm transition-all flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Initiate Cycle Review
              </button>
            )}
          </div>

          {cycleReviewsQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Loading cycle reviews...</div>
          ) : cycleReviewsQuery.data?.length === 0 ? (
            <div className="bg-white p-12 text-center rounded-xl border border-gray-200">
              <RotateCcw className="w-12 h-12 text-gray-400 mx-auto mb-3" />
              <h4 className="text-base font-bold text-gqt-navy">No Cycle Reviews Registered</h4>
              <p className="text-xs text-gray-500 max-w-md mx-auto mt-1">
                Initiate a formal review to freeze historical baseline metrics and bind corrective action items.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {cycleReviewsQuery.data?.map((cycle) => (
                <div
                  key={cycle.id}
                  className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm space-y-4"
                >
                  <div className="flex flex-wrap items-start justify-between gap-2 border-b border-gray-100 pb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-gray-400">{cycle.cycle_code}</span>
                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-blue-50 text-gqt-blue border border-blue-200">
                          {cycle.academic_year}
                        </span>
                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {cycle.status}
                        </span>
                      </div>
                      <h4 className="text-lg font-bold text-gqt-navy mt-1">{cycle.cycle_name}</h4>
                      <p className="text-xs text-gray-500 mt-0.5">
                        Lead Reviewer: <b>{cycle.lead_reviewer_name}</b> | Action items:{' '}
                        <b>
                          {cycle.completed_actions} / {cycle.total_actions} completed
                        </b>
                      </p>
                    </div>

                    {isPlacementHead && (
                      <button
                        onClick={() => setNewActionCycleId(cycle.id)}
                        className="px-3 py-1.5 bg-gqt-blue hover:bg-blue-600 text-white rounded text-xs font-semibold flex items-center gap-1.5"
                      >
                        <Plus className="w-3.5 h-3.5" /> Add Improvement Action
                      </button>
                    )}
                  </div>

                  {/* Baseline metrics snapshot */}
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <span className="text-xs font-bold uppercase text-gray-500">
                      Cycle Baseline Metrics Snapshot (Frozen Provenance)
                    </span>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-2 text-xs">
                      <div>
                        <span className="text-gray-500">Captured Placement Rate:</span>
                        <div className="font-bold text-gqt-navy">
                          {cycle.baseline_metrics_snapshot?.captured_placement_rate ?? 'N/A'}%
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Eligible Population:</span>
                        <div className="font-bold text-gqt-navy">
                          {cycle.baseline_metrics_snapshot?.captured_eligible_count ?? 'N/A'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Distinct Selected:</span>
                        <div className="font-bold text-gqt-navy">
                          {cycle.baseline_metrics_snapshot?.captured_selected_count ?? 'N/A'}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-500">Snapshot Timestamp:</span>
                        <div className="font-bold text-gray-600 truncate">
                          {cycle.baseline_metrics_snapshot?.snapshot_timestamp ?? 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Actions list */}
                  <div>
                    <h5 className="text-xs font-bold text-gray-700 uppercase mb-2">
                      Trackable Action Commitments
                    </h5>
                    {cycle.action_items && cycle.action_items.length > 0 ? (
                      <div className="space-y-2">
                        {cycle.action_items.map((action) => (
                          <div
                            key={action.id}
                            className="p-3 bg-white border border-gray-200 rounded-lg flex flex-wrap items-center justify-between gap-3 text-xs"
                          >
                            <div className="space-y-0.5">
                              <div className="flex items-center gap-2">
                                <span className="font-bold text-gqt-navy">{action.title}</span>
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-gray-100 text-gray-600">
                                  {action.category}
                                </span>
                              </div>
                              <p className="text-gray-600">{action.action_description}</p>
                              {action.success_criteria && (
                                <p className="text-gray-400 text-[11px]">
                                  Criteria: {action.success_criteria}
                                </p>
                              )}
                            </div>

                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded text-xs font-semibold ${
                                  action.status === 'VERIFIED'
                                    ? 'bg-emerald-100 text-emerald-800'
                                    : action.status === 'IN_PROGRESS'
                                    ? 'bg-blue-100 text-blue-800'
                                    : 'bg-gray-100 text-gray-700'
                                }`}
                              >
                                {action.status}
                              </span>

                              {action.status !== 'VERIFIED' && isPlacementHead && (
                                <select
                                  value={action.status}
                                  onChange={(e) =>
                                    updateActionStatusMutation.mutate({
                                      actionId: action.id,
                                      status: e.target.value,
                                    })
                                  }
                                  className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
                                >
                                  <option value="PLANNED">Planned</option>
                                  <option value="IN_PROGRESS">In Progress</option>
                                  <option value="VERIFIED">Verified</option>
                                  <option value="DROPPED">Dropped</option>
                                </select>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">
                        No corrective action items registered for this cycle review.
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* TAB 6: Continuous Improvement Data Diagnostics */}
      {/* ------------------------------------------------------------------- */}
      {activeTab === 'diagnostics' && (
        <div className="space-y-6">
          {diagnosticsQuery.isLoading ? (
            <div className="p-12 text-center text-gray-500">Running diagnostic health checks...</div>
          ) : diagnosticsQuery.isError ? (
            <div className="p-6 bg-rose-50 text-rose-700 rounded-xl border border-rose-200">
              Error running continuous improvement diagnostics.
            </div>
          ) : (
            <>
              {/* Overall Score */}
              <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-6">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-gray-500">
                    Continuous Improvement Data Quality Score
                  </span>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-4xl font-extrabold text-gqt-navy">
                      {diagnosticsQuery.data?.overall_score}%
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-extrabold ${
                        diagnosticsQuery.data?.overall_health === 'HEALTHY'
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {diagnosticsQuery.data?.overall_health}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 max-w-xl">
                    Multi-factor audit inspecting orphaned placement results, dual-submission counts,
                    unresolved offers, small-cohort privacy limits, and unassessed skill demand.
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-gray-400">Diagnostic Timestamp:</span>
                  <div className="text-xs font-mono text-gray-600">
                    {diagnosticsQuery.data?.timestamp}
                  </div>
                </div>
              </div>

              {/* 6 Diagnostic Checks */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {diagnosticsQuery.data?.checks.map((chk) => (
                  <div
                    key={chk.code}
                    className={`p-4 rounded-xl border ${
                      chk.status === 'PASS'
                        ? 'bg-white border-gray-200'
                        : chk.status === 'WARNING'
                        ? 'bg-amber-50/50 border-amber-200'
                        : 'bg-rose-50/50 border-rose-200'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gqt-navy">{chk.name}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-extrabold ${
                          chk.status === 'PASS'
                            ? 'bg-emerald-100 text-emerald-800'
                            : chk.status === 'WARNING'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {chk.status} ({chk.count})
                      </span>
                    </div>

                    <p className="text-xs text-gray-700 mt-2 font-medium">{chk.message}</p>
                    <p className="text-[11px] text-gray-500 mt-1">{chk.impact}</p>

                    <div className="mt-2 pt-2 border-t border-gray-100 text-[11px] text-gqt-blue">
                      <b>Actionable Guidance:</b> {chk.actionable_guidance}
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* MODAL: Draft New Training Plan */}
      {/* ------------------------------------------------------------------- */}
      {isNewPlanModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gqt-navy">Draft Remedial Training Plan</h3>
            <p className="text-xs text-gray-500">
              Plans are created in <b>DRAFT</b> mode and require Placement Head approval before scheduling.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Plan Title</label>
                <input
                  type="text"
                  value={newPlanForm.title}
                  onChange={(e) => setNewPlanForm({ ...newPlanForm, title: e.target.value })}
                  placeholder="e.g. Remedial Data Structures & Problem Solving Workshop"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Target Skill</label>
                  <input
                    type="text"
                    value={newPlanForm.target_skill}
                    onChange={(e) =>
                      setNewPlanForm({ ...newPlanForm, target_skill: e.target.value })
                    }
                    placeholder="e.g. Data Structures"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-gray-700 mb-1">Target Cohort Year</label>
                  <input
                    type="number"
                    value={newPlanForm.target_cohort_year || 2026}
                    onChange={(e) =>
                      setNewPlanForm({
                        ...newPlanForm,
                        target_cohort_year: parseInt(e.target.value) || 2026,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Evidence & Rationale</label>
                <textarea
                  rows={2}
                  value={newPlanForm.evidence_rationale}
                  onChange={(e) =>
                    setNewPlanForm({ ...newPlanForm, evidence_rationale: e.target.value })
                  }
                  placeholder="Document assessment failure rates, recruiter feedback remarks, or unassessed market demand."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Proposed Learning Objectives</label>
                <textarea
                  rows={2}
                  value={newPlanForm.proposed_objectives}
                  onChange={(e) =>
                    setNewPlanForm({ ...newPlanForm, proposed_objectives: e.target.value })
                  }
                  placeholder="Specific learning goals and post-training assessment targets."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
              <button
                onClick={() => setIsNewPlanModalOpen(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-xs font-semibold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                disabled={
                  !newPlanForm.title ||
                  !newPlanForm.target_skill ||
                  !newPlanForm.evidence_rationale ||
                  !newPlanForm.proposed_objectives ||
                  createPlanMutation.isPending
                }
                onClick={() => createPlanMutation.mutate(newPlanForm)}
                className="px-4 py-2 bg-gqt-navy text-white rounded-lg text-xs font-semibold hover:bg-gqt-navy-dark disabled:opacity-50"
              >
                {createPlanMutation.isPending ? 'Saving...' : 'Save Draft Plan'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* MODAL: Plan Approval / Completion Transition */}
      {/* ------------------------------------------------------------------- */}
      {transitionPlan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gqt-navy">
              {transitionPlan.targetStatus === 'APPROVED' ? 'Approve Training Plan' : 'Record Plan Completion'}
            </h3>
            <p className="text-xs text-gray-500">
              Plan: <b>{transitionPlan.plan.title}</b> ({transitionPlan.plan.plan_code})
            </p>

            <div>
              <label className="block font-semibold text-gray-700 mb-1 text-xs">
                {transitionPlan.targetStatus === 'APPROVED' ? 'Approval Notes' : 'Actual Completion Results'}
              </label>
              <textarea
                rows={3}
                value={transitionNotes}
                onChange={(e) => setTransitionNotes(e.target.value)}
                placeholder={
                  transitionPlan.targetStatus === 'APPROVED'
                    ? 'Enter authorization remarks and scheduling instructions.'
                    : 'Document attendance rate, follow-up assessment clearance %, and trainer evaluation.'
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
              <button
                onClick={() => setTransitionPlan(null)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-xs font-semibold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() =>
                  transitionPlanMutation.mutate({
                    planId: transitionPlan.plan.id,
                    status: transitionPlan.targetStatus,
                    notes: transitionNotes,
                  })
                }
                className={`px-4 py-2 text-white rounded-lg text-xs font-semibold ${
                  transitionPlan.targetStatus === 'APPROVED'
                    ? 'bg-gqt-blue hover:bg-blue-600'
                    : 'bg-emerald-600 hover:bg-emerald-700'
                }`}
              >
                {transitionPlanMutation.isPending ? 'Confirming...' : 'Confirm Transition'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* MODAL: Initiate Cycle Review */}
      {/* ------------------------------------------------------------------- */}
      {isNewCycleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gqt-navy">Initiate Recruitment Cycle Review</h3>
            <p className="text-xs text-gray-500">
              Freezes historical baseline metrics and establishes a traceable improvement action log.
            </p>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Cycle Title</label>
                <input
                  type="text"
                  value={newCycleForm.cycle_name}
                  onChange={(e) =>
                    setNewCycleForm({ ...newCycleForm, cycle_name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Academic Year</label>
                <input
                  type="text"
                  value={newCycleForm.academic_year}
                  onChange={(e) =>
                    setNewCycleForm({ ...newCycleForm, academic_year: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Cycle Goals & Target Yields</label>
                <textarea
                  rows={2}
                  value={newCycleForm.goals_and_targets}
                  onChange={(e) =>
                    setNewCycleForm({ ...newCycleForm, goals_and_targets: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Review Summary</label>
                <textarea
                  rows={2}
                  value={newCycleForm.review_summary}
                  onChange={(e) =>
                    setNewCycleForm({ ...newCycleForm, review_summary: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
              <button
                onClick={() => setIsNewCycleModalOpen(false)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-xs font-semibold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                disabled={createCycleMutation.isPending}
                onClick={() => createCycleMutation.mutate()}
                className="px-4 py-2 bg-gqt-navy text-white rounded-lg text-xs font-semibold hover:bg-gqt-navy-dark"
              >
                {createCycleMutation.isPending ? 'Initiating...' : 'Initialize Review'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------- */}
      {/* MODAL: Add Cycle Action Item */}
      {/* ------------------------------------------------------------------- */}
      {newActionCycleId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-gqt-navy">Add Improvement Action Item</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-gray-700 mb-1">Action Title</label>
                <input
                  type="text"
                  value={newActionForm.title}
                  onChange={(e) =>
                    setNewActionForm({ ...newActionForm, title: e.target.value })
                  }
                  placeholder="e.g. Expand Mock Technical Coding Rounds for Product Companies"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Category</label>
                <select
                  value={newActionForm.category}
                  onChange={(e: any) =>
                    setNewActionForm({ ...newActionForm, category: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs bg-white"
                >
                  <option value="CURRICULUM_TRAINING">Curriculum & Remedial Training</option>
                  <option value="INTERVIEW_PREP">Interview Preparation & Mock Drills</option>
                  <option value="CORPORATE_OUTREACH">Corporate Outreach & Partner Pipeline</option>
                  <option value="STUDENT_POLICY">Student Eligibility & Readiness Policy</option>
                  <option value="ASSESSMENT_UPGRADE">Assessment & Diagnostic Upgrades</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Action Description</label>
                <textarea
                  rows={2}
                  value={newActionForm.action_description}
                  onChange={(e) =>
                    setNewActionForm({ ...newActionForm, action_description: e.target.value })
                  }
                  placeholder="Concrete operational steps to be taken."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block font-semibold text-gray-700 mb-1">Success Criteria</label>
                <input
                  type="text"
                  value={newActionForm.success_criteria}
                  onChange={(e) =>
                    setNewActionForm({ ...newActionForm, success_criteria: e.target.value })
                  }
                  placeholder="Measurable indicator of completion."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-gray-100">
              <button
                onClick={() => setNewActionCycleId(null)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg text-xs font-semibold hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                disabled={
                  !newActionForm.title ||
                  !newActionForm.action_description ||
                  createActionMutation.isPending
                }
                onClick={() => createActionMutation.mutate(newActionCycleId)}
                className="px-4 py-2 bg-gqt-blue text-white rounded-lg text-xs font-semibold hover:bg-blue-600 disabled:opacity-50"
              >
                {createActionMutation.isPending ? 'Binding...' : 'Commit Action'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
