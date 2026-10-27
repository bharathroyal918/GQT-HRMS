import React, { useState, useEffect, useCallback } from 'react';
import {
  MessageSquare,
  Star,
  Users,
  Building2,
  GraduationCap,
  Sparkles,
  Search,
  Filter,
  Plus,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Eye,
  EyeOff,
  Award,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge, StatusVariant } from '../../components/common/StatusBadge';
import { feedbackApi } from '../../api/feedbackApi';
import { useAuth } from '../../context/AuthContext';
import {
  StudentFeedback,
  HRFeedback,
  TrainerFeedback,
  FeedbackKPIs,
  StudentEligibleDrive,
  DifficultyLevel,
  CandidateQuality,
  StudentReadiness,
} from '../../types/feedback';

export const FeedbackWorkspacePage: React.FC = () => {
  const { user, hasAnyRole } = useAuth();

  const isStaff = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']);
  const isStudent = !isStaff && !!user?.roles.includes('STUDENT');
  const isTrainerOnly = !isStaff && (!!user?.roles.includes('TRAINER') || !!user?.roles.includes('EVALUATOR'));
  const isHROnly = !isStaff && !!user?.roles.includes('HR_RELATIONSHIP_MGR');
  const isAuditor = !isStaff && !!user?.roles.includes('AUDITOR');

  const [activeTab, setActiveTab] = useState<'student' | 'hr' | 'trainer'>('student');

  useEffect(() => {
    if (isStudent) {
      setActiveTab('student');
    } else if (isTrainerOnly) {
      setActiveTab('trainer');
    } else if (isHROnly) {
      setActiveTab('hr');
    }
  }, [isStudent, isTrainerOnly, isHROnly]);

  // Loading & Global States
  const [isLoading, setIsLoading] = useState(true);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Data States
  const [kpis, setKpis] = useState<FeedbackKPIs | null>(null);
  const [studentFeedbacks, setStudentFeedbacks] = useState<StudentFeedback[]>([]);
  const [hrFeedbacks, setHrFeedbacks] = useState<HRFeedback[]>([]);
  const [trainerFeedbacks, setTrainerFeedbacks] = useState<TrainerFeedback[]>([]);
  const [eligibleDrives, setEligibleDrives] = useState<StudentEligibleDrive[]>([]);

  // Search & Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState<string>('ALL');
  const [qualityFilter, setQualityFilter] = useState<string>('ALL');
  const [readinessFilter, setReadinessFilter] = useState<string>('ALL');

  // Modals
  const [isStudentModalOpen, setIsStudentModalOpen] = useState(false);
  const [isHRModalOpen, setIsHRModalOpen] = useState(false);
  const [isTrainerModalOpen, setIsTrainerModalOpen] = useState(false);

  // Detail Modal for reading long feedback
  const [selectedRecord, setSelectedRecord] = useState<{
    title: string;
    category: string;
    author: string;
    date: string;
    items: { label: string; value: string | number }[];
  } | null>(null);

  // Student Form State
  const [studentFormData, setStudentFormData] = useState({
    company: '',
    job_requirement: '',
    interview_schedule: '',
    interview_round: '',
    interview_experience: '',
    technical_questions: '',
    difficulty: 'MEDIUM' as DifficultyLevel,
    suggestions: '',
    is_anonymous: false,
  });

  // HR Form State
  const [hrFormData, setHrFormData] = useState({
    company: '',
    hr_contact: '',
    job_requirement: '',
    candidate: '',
    candidate_quality: 'GOOD' as CandidateQuality,
    candidate_quality_remarks: '',
    technical_skills_rating: 4,
    technical_skills_remarks: '',
    communication_skills_rating: 4,
    communication_skills_remarks: '',
    hiring_satisfaction_rating: 4,
    hiring_satisfaction_remarks: '',
  });

  // Trainer Form State
  const [trainerFormData, setTrainerFormData] = useState({
    student: '',
    training_session: '',
    student_readiness: 'READY' as StudentReadiness,
    student_readiness_remarks: '',
    training_effectiveness_rating: 4,
    training_effectiveness_remarks: '',
    areas_for_improvement: '',
  });

  // Fetch all feedback data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      // 1. Fetch KPIs if permitted (staff, HR, trainer, auditor)
      if (!isStudent) {
        feedbackApi.getKPIs().then(setKpis).catch(() => null);
      }

      // 2. Fetch category data according to active tab and permissions
      if (activeTab === 'student' || isStaff) {
        const studentData = await feedbackApi.listStudentFeedback({
          difficulty: difficultyFilter !== 'ALL' ? difficultyFilter : undefined,
          search: searchQuery || undefined,
        });
        setStudentFeedbacks(studentData);
      }

      if ((activeTab === 'hr' || isStaff) && !isStudent && !isTrainerOnly) {
        const hrData = await feedbackApi.listHRFeedback({
          candidate_quality: qualityFilter !== 'ALL' ? qualityFilter : undefined,
          search: searchQuery || undefined,
        });
        setHrFeedbacks(hrData);
      }

      if ((activeTab === 'trainer' || isStaff) && !isStudent && !isHROnly) {
        const trainerData = await feedbackApi.listTrainerFeedback({
          student_readiness: readinessFilter !== 'ALL' ? readinessFilter : undefined,
          search: searchQuery || undefined,
        });
        setTrainerFeedbacks(trainerData);
      }

      // 3. If student, fetch eligible drives for self-service
      if (isStudent || isStaff) {
        feedbackApi.getStudentEligibleDrives().then(setEligibleDrives).catch(() => []);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load feedback records.');
    } finally {
      setIsLoading(false);
    }
  }, [activeTab, isStudent, isStaff, isTrainerOnly, isHROnly, difficultyFilter, qualityFilter, readinessFilter, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Form Submissions
  const handleStudentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!studentFormData.company.trim()) {
      setError('Company name / ID is required.');
      return;
    }
    if (studentFormData.interview_experience.trim().length < 10) {
      setError('Interview experience narrative must be at least 10 characters.');
      return;
    }

    setIsActionLoading(true);
    setError(null);
    try {
      await feedbackApi.submitStudentFeedback({
        company: studentFormData.company.trim(),
        job_requirement: studentFormData.job_requirement.trim() || null,
        interview_schedule: studentFormData.interview_schedule.trim() || null,
        interview_round: studentFormData.interview_round.trim() || null,
        interview_experience: studentFormData.interview_experience.trim(),
        technical_questions: studentFormData.technical_questions.trim() || undefined,
        difficulty: studentFormData.difficulty,
        suggestions: studentFormData.suggestions.trim() || undefined,
        is_anonymous: studentFormData.is_anonymous,
      });
      setActionSuccess('Interview experience feedback submitted successfully!');
      setIsStudentModalOpen(false);
      setStudentFormData({
        company: '',
        job_requirement: '',
        interview_schedule: '',
        interview_round: '',
        interview_experience: '',
        technical_questions: '',
        difficulty: 'MEDIUM',
        suggestions: '',
        is_anonymous: false,
      });
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to submit student feedback.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleHRSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hrFormData.company.trim()) {
      setError('Company ID is required.');
      return;
    }
    setIsActionLoading(true);
    setError(null);
    try {
      await feedbackApi.submitHRFeedback({
        company: hrFormData.company.trim(),
        hr_contact: hrFormData.hr_contact.trim() || null,
        job_requirement: hrFormData.job_requirement.trim() || null,
        candidate: hrFormData.candidate.trim() || null,
        candidate_quality: hrFormData.candidate_quality,
        candidate_quality_remarks: hrFormData.candidate_quality_remarks.trim() || undefined,
        technical_skills_rating: Number(hrFormData.technical_skills_rating),
        technical_skills_remarks: hrFormData.technical_skills_remarks.trim() || undefined,
        communication_skills_rating: Number(hrFormData.communication_skills_rating),
        communication_skills_remarks: hrFormData.communication_skills_remarks.trim() || undefined,
        hiring_satisfaction_rating: Number(hrFormData.hiring_satisfaction_rating),
        hiring_satisfaction_remarks: hrFormData.hiring_satisfaction_remarks.trim() || undefined,
      });
      setActionSuccess('Corporate HR evaluation recorded successfully!');
      setIsHRModalOpen(false);
      setHrFormData({
        company: '',
        hr_contact: '',
        job_requirement: '',
        candidate: '',
        candidate_quality: 'GOOD',
        candidate_quality_remarks: '',
        technical_skills_rating: 4,
        technical_skills_remarks: '',
        communication_skills_rating: 4,
        communication_skills_remarks: '',
        hiring_satisfaction_rating: 4,
        hiring_satisfaction_remarks: '',
      });
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to submit HR feedback.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const handleTrainerSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trainerFormData.student.trim()) {
      setError('Student ID / Profile ID is required.');
      return;
    }
    if (trainerFormData.areas_for_improvement.trim().length < 10) {
      setError('Areas for improvement must be at least 10 characters.');
      return;
    }
    setIsActionLoading(true);
    setError(null);
    try {
      await feedbackApi.submitTrainerFeedback({
        student: trainerFormData.student.trim(),
        training_session: trainerFormData.training_session.trim() || null,
        student_readiness: trainerFormData.student_readiness,
        student_readiness_remarks: trainerFormData.student_readiness_remarks.trim() || undefined,
        training_effectiveness_rating: Number(trainerFormData.training_effectiveness_rating),
        training_effectiveness_remarks: trainerFormData.training_effectiveness_remarks.trim() || undefined,
        areas_for_improvement: trainerFormData.areas_for_improvement.trim(),
      });
      setActionSuccess('Trainer evaluation submitted successfully!');
      setIsTrainerModalOpen(false);
      setTrainerFormData({
        student: '',
        training_session: '',
        student_readiness: 'READY',
        student_readiness_remarks: '',
        training_effectiveness_rating: 4,
        training_effectiveness_remarks: '',
        areas_for_improvement: '',
      });
      fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to submit trainer feedback.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Helper Badge Colors
  const getDifficultyBadge = (difficulty: DifficultyLevel): { variant: StatusVariant; label: string } => {
    switch (difficulty) {
      case 'EASY':
        return { variant: 'success', label: 'Easy' };
      case 'MEDIUM':
        return { variant: 'info', label: 'Medium' };
      case 'HARD':
        return { variant: 'warning', label: 'Hard' };
      case 'VERY_HARD':
        return { variant: 'danger', label: 'Very Hard' };
      default:
        return { variant: 'neutral', label: difficulty };
    }
  };

  const getQualityBadge = (quality: CandidateQuality): { variant: StatusVariant; label: string } => {
    switch (quality) {
      case 'EXCELLENT':
        return { variant: 'success', label: 'Excellent' };
      case 'GOOD':
        return { variant: 'info', label: 'Good' };
      case 'FAIR':
        return { variant: 'warning', label: 'Fair' };
      case 'POOR':
        return { variant: 'danger', label: 'Poor' };
      default:
        return { variant: 'neutral', label: quality };
    }
  };

  const getReadinessBadge = (readiness: StudentReadiness): { variant: StatusVariant; label: string } => {
    switch (readiness) {
      case 'HIGHLY_READY':
        return { variant: 'success', label: 'Highly Ready' };
      case 'READY':
        return { variant: 'info', label: 'Ready' };
      case 'NEEDS_PRACTICE':
        return { variant: 'warning', label: 'Needs Practice' };
      case 'NOT_READY':
        return { variant: 'danger', label: 'Not Ready' };
      default:
        return { variant: 'neutral', label: readiness };
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex items-center gap-0.5 text-amber-500">
        {[1, 2, 3, 4, 5].map((s) => (
          <Star
            key={s}
            className={`w-3.5 h-3.5 ${s <= rating ? 'fill-amber-400 text-amber-500' : 'text-slate-300'}`}
          />
        ))}
        <span className="ml-1 text-xs font-semibold text-slate-700">{rating}/5</span>
      </div>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase tracking-wider bg-gqt-blue-light text-gqt-blue">
              Phase 9
            </span>
            <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Feedback Collection Workspace</h1>
          </div>
          <p className="text-sm text-gqt-neutral-500 mt-1">
            Official feedback collection module spanning Student Interview Experiences, Corporate HR Recruiter
            Evaluations, and Trainer Readiness Feedback.
          </p>
        </div>

        {/* Global Action Buttons */}
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            disabled={isLoading}
            className="flex items-center gap-1.5"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {!isAuditor && isStudent && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsStudentModalOpen(true)}
              className="flex items-center gap-1.5 bg-gqt-blue hover:bg-blue-700 text-white"
            >
              <Plus className="w-4 h-4" />
              Share Interview Experience
            </Button>
          )}

          {!isAuditor && !isStudent && (
            <>
              {activeTab === 'student' && isStaff && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsStudentModalOpen(true)}
                  className="flex items-center gap-1.5 bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4" />
                  Add Student Feedback
                </Button>
              )}
              {activeTab === 'hr' && (isHROnly || isStaff) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsHRModalOpen(true)}
                  className="flex items-center gap-1.5 bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4" />
                  Record HR Feedback
                </Button>
              )}
              {activeTab === 'trainer' && (isTrainerOnly || isStaff) && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => setIsTrainerModalOpen(true)}
                  className="flex items-center gap-1.5 bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  <Plus className="w-4 h-4" />
                  Record Trainer Feedback
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-600 hover:text-rose-800 font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-600 hover:text-emerald-800 font-bold ml-4">
            ×
          </button>
        </div>
      )}

      {/* Metric / KPI Banner (Authorized non-student roles) */}
      {!isStudent && kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <MessageSquare className="w-4 h-4 text-gqt-blue" />
              Student Feedback
            </div>
            <div className="text-2xl font-black text-gqt-navy mt-1">{kpis.total_student_feedback}</div>
            <div className="text-xs text-slate-400 mt-0.5">Interview experiences</div>
          </Card>

          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <Building2 className="w-4 h-4 text-indigo-600" />
              HR Evaluations
            </div>
            <div className="text-2xl font-black text-gqt-navy mt-1">{kpis.total_hr_feedback}</div>
            <div className="text-xs text-slate-400 mt-0.5">Recruiter feedbacks</div>
          </Card>

          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <Users className="w-4 h-4 text-emerald-600" />
              Trainer Feedback
            </div>
            <div className="text-2xl font-black text-gqt-navy mt-1">{kpis.total_trainer_feedback}</div>
            <div className="text-xs text-slate-400 mt-0.5">Readiness audits</div>
          </Card>

          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <Star className="w-4 h-4 text-amber-500" />
              Avg Tech Rating
            </div>
            <div className="text-2xl font-black text-amber-600 mt-1">
              {kpis.avg_technical_skills_rating.toFixed(1)}
              <span className="text-xs text-slate-400 font-normal"> / 5.0</span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Recruiter technical score</div>
          </Card>

          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <Sparkles className="w-4 h-4 text-blue-500" />
              Avg Comm Rating
            </div>
            <div className="text-2xl font-black text-blue-600 mt-1">
              {kpis.avg_communication_skills_rating.toFixed(1)}
              <span className="text-xs text-slate-400 font-normal"> / 5.0</span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Recruiter comm score</div>
          </Card>

          <Card elevation="sm" className="p-4 bg-white border border-slate-200">
            <div className="flex items-center gap-2 text-slate-500 text-xs font-semibold uppercase">
              <Award className="w-4 h-4 text-emerald-500" />
              Avg Satisfaction
            </div>
            <div className="text-2xl font-black text-emerald-600 mt-1">
              {kpis.avg_hiring_satisfaction_rating.toFixed(1)}
              <span className="text-xs text-slate-400 font-normal"> / 5.0</span>
            </div>
            <div className="text-xs text-slate-400 mt-0.5">Overall hiring satisfaction</div>
          </Card>
        </div>
      )}

      {/* Role-Aware Category Tabs */}
      <div className="border-b border-gqt-neutral-200">
        <nav className="flex space-x-8" aria-label="Feedback Categories">
          {(!isTrainerOnly && !isHROnly) && (
            <button
              onClick={() => setActiveTab('student')}
              className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'student'
                  ? 'border-gqt-blue text-gqt-blue font-bold'
                  : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-700 hover:border-gqt-neutral-300'
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              {isStudent ? 'My Interview Experiences' : 'Student Interview Experiences'}
              <span className="ml-1.5 py-0.5 px-2 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
                {studentFeedbacks.length}
              </span>
            </button>
          )}

          {!isStudent && !isTrainerOnly && (
            <button
              onClick={() => setActiveTab('hr')}
              className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'hr'
                  ? 'border-gqt-blue text-gqt-blue font-bold'
                  : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-700 hover:border-gqt-neutral-300'
              }`}
            >
              <Building2 className="w-4 h-4" />
              Corporate HR Feedback
              <span className="ml-1.5 py-0.5 px-2 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
                {hrFeedbacks.length}
              </span>
            </button>
          )}

          {!isStudent && !isHROnly && (
            <button
              onClick={() => setActiveTab('trainer')}
              className={`py-3 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === 'trainer'
                  ? 'border-gqt-blue text-gqt-blue font-bold'
                  : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-700 hover:border-gqt-neutral-300'
              }`}
            >
              <Users className="w-4 h-4" />
              Trainer Readiness Feedback
              <span className="ml-1.5 py-0.5 px-2 rounded-full text-xs font-semibold bg-slate-100 text-slate-600">
                {trainerFeedbacks.length}
              </span>
            </button>
          )}
        </nav>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-white p-3 rounded-lg border border-slate-200">
        <div className="relative flex-1">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder={`Search ${activeTab} feedback...`}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-sm rounded-md border border-slate-200 focus:outline-none focus:ring-2 focus:ring-gqt-blue focus:border-transparent"
          />
        </div>

        {activeTab === 'student' && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              aria-label="Filter by interview difficulty"
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              className="text-xs rounded border border-slate-200 py-1.5 px-2.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-gqt-blue"
            >
              <option value="ALL">All Difficulties</option>
              <option value="EASY">Easy</option>
              <option value="MEDIUM">Medium</option>
              <option value="HARD">Hard</option>
              <option value="VERY_HARD">Very Hard</option>
            </select>
          </div>
        )}

        {activeTab === 'hr' && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              aria-label="Filter by candidate quality"
              value={qualityFilter}
              onChange={(e) => setQualityFilter(e.target.value)}
              className="text-xs rounded border border-slate-200 py-1.5 px-2.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-gqt-blue"
            >
              <option value="ALL">All Candidate Qualities</option>
              <option value="EXCELLENT">Excellent</option>
              <option value="GOOD">Good</option>
              <option value="FAIR">Fair</option>
              <option value="POOR">Poor</option>
            </select>
          </div>
        )}

        {activeTab === 'trainer' && (
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              aria-label="Filter by student readiness"
              value={readinessFilter}
              onChange={(e) => setReadinessFilter(e.target.value)}
              className="text-xs rounded border border-slate-200 py-1.5 px-2.5 bg-white text-slate-700 focus:outline-none focus:ring-1 focus:ring-gqt-blue"
            >
              <option value="ALL">All Readiness Levels</option>
              <option value="HIGHLY_READY">Highly Ready</option>
              <option value="READY">Ready</option>
              <option value="NEEDS_PRACTICE">Needs Practice</option>
              <option value="NOT_READY">Not Ready</option>
            </select>
          </div>
        )}
      </div>

      {/* Main Tab Content */}
      {isLoading ? (
        <div className="p-12 text-center">
          <RefreshCw className="w-8 h-8 text-gqt-blue animate-spin mx-auto mb-2" />
          <p className="text-sm text-slate-500">Loading feedback records...</p>
        </div>
      ) : (
        <>
          {/* TAB 1: Student Interview Experiences */}
          {activeTab === 'student' && (
            <div className="space-y-4">
              {studentFeedbacks.length === 0 ? (
                <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
                  <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-700">No Student Interview Feedback Found</h3>
                  <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                    {isStudent
                      ? 'You have not submitted any interview experiences yet. Click "Share Interview Experience" to contribute.'
                      : 'No student feedback has been submitted matching the current filters.'}
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {studentFeedbacks.map((item) => {
                    const badge = getDifficultyBadge(item.difficulty);
                    return (
                      <Card key={item.id} elevation="sm" className="bg-white border border-slate-200 flex flex-col justify-between">
                        <CardHeader className="p-4 border-b border-slate-100 flex flex-row items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-gqt-navy text-base">{item.company_name}</h4>
                              {item.job_title && (
                                <span className="text-xs text-slate-500">({item.job_title})</span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                              <span>Candidate: <strong className="text-slate-700">{item.student_name}</strong></span>
                              {item.is_anonymous && (
                                <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                                  <EyeOff className="w-3 h-3 text-slate-400" />
                                  Anonymous
                                </span>
                              )}
                            </div>
                          </div>
                          <StatusBadge variant={badge.variant} label={badge.label} />
                        </CardHeader>

                        <CardContent className="p-4 space-y-3 flex-1">
                          {/* Interview Experience */}
                          <div>
                            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                              Interview Experience
                            </span>
                            <p className="text-sm text-slate-700 line-clamp-3 bg-slate-50 p-2 rounded border border-slate-100">
                              {item.interview_experience}
                            </p>
                          </div>

                          {/* Technical Questions */}
                          {item.technical_questions && (
                            <div>
                              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                                Technical Questions
                              </span>
                              <p className="text-sm text-slate-700 line-clamp-2 bg-slate-50 p-2 rounded border border-slate-100">
                                {item.technical_questions}
                              </p>
                            </div>
                          )}

                          {/* Suggestions */}
                          {item.suggestions && (
                            <div>
                              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                                Suggestions for Juniors
                              </span>
                              <p className="text-xs text-slate-600 line-clamp-2 italic">
                                &ldquo;{item.suggestions}&rdquo;
                              </p>
                            </div>
                          )}
                        </CardContent>

                        <div className="px-4 py-2.5 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>
                            {item.interview_date ? `Interview Date: ${item.interview_date}` : `Submitted: ${new Date(item.created_at).toLocaleDateString()}`}
                          </span>
                          <button
                            onClick={() =>
                              setSelectedRecord({
                                title: `${item.company_name} — Interview Experience`,
                                category: 'Student Interview Feedback',
                                author: item.student_name,
                                date: new Date(item.created_at).toLocaleString(),
                                items: [
                                  { label: 'Company', value: item.company_name },
                                  { label: 'Job Title', value: item.job_title || 'N/A' },
                                  { label: 'Interview Round', value: item.interview_round || 'General / All Rounds' },
                                  { label: 'Difficulty', value: item.difficulty_display },
                                  { label: 'Anonymous', value: item.is_anonymous ? 'Yes' : 'No' },
                                  { label: 'Interview Experience', value: item.interview_experience },
                                  { label: 'Technical Questions Asked', value: item.technical_questions || 'None specified' },
                                  { label: 'Suggestions', value: item.suggestions || 'None' },
                                ],
                              })
                            }
                            className="font-semibold text-gqt-blue hover:underline flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View Full
                          </button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Corporate HR Feedback */}
          {activeTab === 'hr' && (
            <div className="space-y-4">
              {hrFeedbacks.length === 0 ? (
                <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
                  <Building2 className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-700">No Corporate HR Feedback Found</h3>
                  <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                    No HR feedback records match your assigned scope or filters.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {hrFeedbacks.map((item) => {
                    const qualityBadge = getQualityBadge(item.candidate_quality);
                    return (
                      <Card key={item.id} elevation="sm" className="bg-white border border-slate-200 flex flex-col justify-between">
                        <CardHeader className="p-4 border-b border-slate-100 flex flex-row items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-gqt-navy text-base">{item.company_name}</h4>
                              {item.job_title && (
                                <span className="text-xs text-slate-500">({item.job_title})</span>
                              )}
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5">
                              {item.candidate_name ? (
                                <span>Candidate: <strong className="text-slate-700">{item.candidate_name}</strong> ({item.candidate_roll_number})</span>
                              ) : (
                                <span className="italic text-slate-400">General Candidate Cohort</span>
                              )}
                            </div>
                          </div>
                          <StatusBadge variant={qualityBadge.variant} label={qualityBadge.label} />
                        </CardHeader>

                        <CardContent className="p-4 space-y-3 flex-1">
                          {/* Structured Rating Scores */}
                          <div className="grid grid-cols-3 gap-2 bg-slate-50 p-2.5 rounded border border-slate-100">
                            <div>
                              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Technical</span>
                              {renderStars(item.technical_skills_rating)}
                            </div>
                            <div>
                              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Communication</span>
                              {renderStars(item.communication_skills_rating)}
                            </div>
                            <div>
                              <span className="text-[11px] font-semibold text-slate-500 uppercase block">Satisfaction</span>
                              {renderStars(item.hiring_satisfaction_rating)}
                            </div>
                          </div>

                          {/* Candidate Quality Remarks */}
                          {item.candidate_quality_remarks && (
                            <div>
                              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                                Candidate Quality Remarks
                              </span>
                              <p className="text-xs text-slate-700 line-clamp-2 bg-slate-50 p-2 rounded">
                                {item.candidate_quality_remarks}
                              </p>
                            </div>
                          )}

                          {/* Technical & Communication Remarks */}
                          {(item.technical_skills_remarks || item.communication_skills_remarks) && (
                            <div className="text-xs text-slate-600 space-y-1">
                              {item.technical_skills_remarks && (
                                <p><strong className="text-slate-700">Tech Remarks:</strong> {item.technical_skills_remarks}</p>
                              )}
                              {item.communication_skills_remarks && (
                                <p><strong className="text-slate-700">Comm Remarks:</strong> {item.communication_skills_remarks}</p>
                              )}
                            </div>
                          )}
                        </CardContent>

                        <div className="px-4 py-2.5 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>Evaluator: <strong>{item.submitted_by_name}</strong></span>
                          <button
                            onClick={() =>
                              setSelectedRecord({
                                title: `${item.company_name} — HR Evaluation`,
                                category: 'Corporate HR Feedback',
                                author: item.submitted_by_name,
                                date: new Date(item.created_at).toLocaleString(),
                                items: [
                                  { label: 'Company', value: item.company_name },
                                  { label: 'HR Contact', value: item.hr_contact_name || 'N/A' },
                                  { label: 'Candidate', value: item.candidate_name ? `${item.candidate_name} (${item.candidate_roll_number})` : 'Cohort' },
                                  { label: 'Candidate Quality', value: item.candidate_quality_display },
                                  { label: 'Quality Remarks', value: item.candidate_quality_remarks || 'None' },
                                  { label: 'Technical Skills Rating', value: `${item.technical_skills_rating} / 5` },
                                  { label: 'Technical Skills Remarks', value: item.technical_skills_remarks || 'None' },
                                  { label: 'Communication Skills Rating', value: `${item.communication_skills_rating} / 5` },
                                  { label: 'Communication Skills Remarks', value: item.communication_skills_remarks || 'None' },
                                  { label: 'Hiring Satisfaction Rating', value: `${item.hiring_satisfaction_rating} / 5` },
                                  { label: 'Hiring Satisfaction Remarks', value: item.hiring_satisfaction_remarks || 'None' },
                                ],
                              })
                            }
                            className="font-semibold text-gqt-blue hover:underline flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View Full
                          </button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Trainer Feedback */}
          {activeTab === 'trainer' && (
            <div className="space-y-4">
              {trainerFeedbacks.length === 0 ? (
                <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
                  <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <h3 className="text-base font-bold text-slate-700">No Trainer Feedback Found</h3>
                  <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                    No trainer evaluations match your authorized assignment scope or filters.
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {trainerFeedbacks.map((item) => {
                    const readinessBadge = getReadinessBadge(item.student_readiness);
                    return (
                      <Card key={item.id} elevation="sm" className="bg-white border border-slate-200 flex flex-col justify-between">
                        <CardHeader className="p-4 border-b border-slate-100 flex flex-row items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="font-bold text-gqt-navy text-base">{item.student_name}</h4>
                              <span className="text-xs font-mono text-slate-500">({item.student_roll_number})</span>
                            </div>
                            <div className="text-xs text-slate-500 mt-0.5">
                              {item.session_title ? (
                                <span>Session: <strong className="text-slate-700">{item.session_title}</strong></span>
                              ) : (
                                <span>General Assessment Cycle</span>
                              )}
                            </div>
                          </div>
                          <StatusBadge variant={readinessBadge.variant} label={readinessBadge.label} />
                        </CardHeader>

                        <CardContent className="p-4 space-y-3 flex-1">
                          {/* Training Effectiveness Rating */}
                          <div className="flex items-center justify-between bg-slate-50 p-2.5 rounded border border-slate-100">
                            <span className="text-xs font-semibold text-slate-500 uppercase">Training Effectiveness</span>
                            {renderStars(item.training_effectiveness_rating)}
                          </div>

                          {/* Student Readiness Remarks */}
                          {item.student_readiness_remarks && (
                            <div>
                              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                                Readiness Assessment
                              </span>
                              <p className="text-xs text-slate-700 line-clamp-2 bg-slate-50 p-2 rounded">
                                {item.student_readiness_remarks}
                              </p>
                            </div>
                          )}

                          {/* Concrete Areas for Improvement */}
                          <div>
                            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-0.5">
                              Areas for Improvement
                            </span>
                            <p className="text-xs text-slate-700 line-clamp-3 bg-amber-50/60 border border-amber-100 p-2 rounded">
                              {item.areas_for_improvement}
                            </p>
                          </div>
                        </CardContent>

                        <div className="px-4 py-2.5 bg-slate-50/70 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
                          <span>Trainer: <strong>{item.trainer_name}</strong></span>
                          <button
                            onClick={() =>
                              setSelectedRecord({
                                title: `${item.student_name} — Trainer Evaluation`,
                                category: 'Trainer Readiness Feedback',
                                author: item.trainer_name,
                                date: new Date(item.created_at).toLocaleString(),
                                items: [
                                  { label: 'Student', value: `${item.student_name} (${item.student_roll_number})` },
                                  { label: 'Session / Cohort', value: item.session_title || 'General Cycle' },
                                  { label: 'Student Readiness', value: item.student_readiness_display },
                                  { label: 'Readiness Remarks', value: item.student_readiness_remarks || 'None' },
                                  { label: 'Training Effectiveness Rating', value: `${item.training_effectiveness_rating} / 5` },
                                  { label: 'Effectiveness Remarks', value: item.training_effectiveness_remarks || 'None' },
                                  { label: 'Areas for Improvement', value: item.areas_for_improvement },
                                ],
                              })
                            }
                            className="font-semibold text-gqt-blue hover:underline flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View Full
                          </button>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* MODAL 1: Submit Student Feedback */}
      {isStudentModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden my-8 border border-slate-200">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gqt-navy text-lg">Share Interview Experience</h3>
                <p className="text-xs text-slate-500 mt-0.5">Category A: Technical questions, difficulty, suggestions</p>
              </div>
              <button
                onClick={() => setIsStudentModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleStudentSubmit} className="p-5 space-y-4">
              {/* Eligible Drive Selector if available */}
              {eligibleDrives.length > 0 ? (
                <div>
                  <label htmlFor="student-form-drive-select" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Select Attended Interview Drive *
                  </label>
                  <select
                    id="student-form-drive-select"
                    className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                    value={studentFormData.interview_schedule}
                    onChange={(e) => {
                      const selected = eligibleDrives.find((d) => d.interview_schedule_id === e.target.value);
                      if (selected) {
                        setStudentFormData({
                          ...studentFormData,
                          interview_schedule: selected.interview_schedule_id,
                          company: selected.company_id || selected.company_name,
                          job_requirement: selected.job_requirement_id || '',
                        });
                      } else {
                        setStudentFormData({
                          ...studentFormData,
                          interview_schedule: '',
                        });
                      }
                    }}
                  >
                    <option value="">-- Choose from your attended interview schedules --</option>
                    {eligibleDrives.map((d) => (
                      <option key={d.interview_schedule_id} value={d.interview_schedule_id}>
                        {d.company_name} — {d.job_title} ({d.interview_date})
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              {/* Company Name / ID */}
              <div>
                <label htmlFor="student-form-company" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Company Name / ID *
                </label>
                <input
                  id="student-form-company"
                  type="text"
                  required
                  placeholder="e.g. Acme Tech Solutions"
                  value={studentFormData.company}
                  onChange={(e) => setStudentFormData({ ...studentFormData, company: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Difficulty Level */}
              <div>
                <label htmlFor="student-form-difficulty" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Interview Difficulty *
                </label>
                <select
                  id="student-form-difficulty"
                  value={studentFormData.difficulty}
                  onChange={(e) => setStudentFormData({ ...studentFormData, difficulty: e.target.value as DifficultyLevel })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="EASY">Easy — Basic conceptual questions</option>
                  <option value="MEDIUM">Medium — Standard problem solving & domain theory</option>
                  <option value="HARD">Hard — Rigorous DSA / architecture challenges</option>
                  <option value="VERY_HARD">Very Hard — Advanced live coding & deep edge cases</option>
                </select>
              </div>

              {/* Technical Questions */}
              <div>
                <label htmlFor="student-form-tech-questions" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Technical Questions Asked
                </label>
                <textarea
                  id="student-form-tech-questions"
                  rows={3}
                  placeholder="e.g. Reverse a linked list; SQL indexing strategies; Microservices transactions..."
                  value={studentFormData.technical_questions}
                  onChange={(e) => setStudentFormData({ ...studentFormData, technical_questions: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Interview Experience */}
              <div>
                <label htmlFor="student-form-experience" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Interview Experience Narrative * (min 10 characters)
                </label>
                <textarea
                  id="student-form-experience"
                  required
                  rows={3}
                  placeholder="Describe the interviewer demeanor, structure of rounds, time allocation..."
                  value={studentFormData.interview_experience}
                  onChange={(e) => setStudentFormData({ ...studentFormData, interview_experience: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Suggestions for Juniors */}
              <div>
                <label htmlFor="student-form-suggestions" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Suggestions for Junior Batches
                </label>
                <textarea
                  id="student-form-suggestions"
                  rows={2}
                  placeholder="e.g. Focus on OOPs solid principles and live code cleanliness..."
                  value={studentFormData.suggestions}
                  onChange={(e) => setStudentFormData({ ...studentFormData, suggestions: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Anonymity Option */}
              <div className="flex items-start gap-2 pt-2 border-t border-slate-100">
                <input
                  type="checkbox"
                  id="is_anonymous"
                  checked={studentFormData.is_anonymous}
                  onChange={(e) => setStudentFormData({ ...studentFormData, is_anonymous: e.target.checked })}
                  className="mt-1 h-4 w-4 text-gqt-blue focus:ring-gqt-blue border-slate-300 rounded"
                />
                <label htmlFor="is_anonymous" className="text-xs text-slate-600 cursor-pointer">
                  <span className="font-semibold text-slate-800">Submit Anonymously</span>
                  <br />
                  Hide my name and roll number from peers and companies (only placement admin retains moderation access).
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsStudentModalOpen(false)}
                  disabled={isActionLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading}
                  className="bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  {isActionLoading ? 'Submitting...' : 'Submit Feedback'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 2: Submit HR Feedback */}
      {isHRModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden my-8 border border-slate-200">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gqt-navy text-lg">Record Corporate HR Feedback</h3>
                <p className="text-xs text-slate-500 mt-0.5">Category B: Candidate quality, tech skills, communication, satisfaction</p>
              </div>
              <button
                onClick={() => setIsHRModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleHRSubmit} className="p-5 space-y-4">
              {/* Company ID */}
              <div>
                <label htmlFor="hr-form-company" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Company ID / Name *
                </label>
                <input
                  id="hr-form-company"
                  type="text"
                  required
                  placeholder="Company UUID or Name"
                  value={hrFormData.company}
                  onChange={(e) => setHrFormData({ ...hrFormData, company: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Candidate ID (Optional) */}
              <div>
                <label htmlFor="hr-form-candidate" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Candidate ID (Optional — leave blank for cohort level)
                </label>
                <input
                  id="hr-form-candidate"
                  type="text"
                  placeholder="Candidate Shortlist or Student Profile UUID"
                  value={hrFormData.candidate}
                  onChange={(e) => setHrFormData({ ...hrFormData, candidate: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Candidate Quality */}
              <div>
                <label htmlFor="hr-form-candidate-quality" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Candidate Quality *
                </label>
                <select
                  id="hr-form-candidate-quality"
                  value={hrFormData.candidate_quality}
                  onChange={(e) => setHrFormData({ ...hrFormData, candidate_quality: e.target.value as CandidateQuality })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="EXCELLENT">Excellent — Top quartile capability</option>
                  <option value="GOOD">Good — Met technical hiring benchmark</option>
                  <option value="FAIR">Fair — Borderline readiness</option>
                  <option value="POOR">Poor — Significant skill gaps</option>
                </select>
              </div>

              {/* Ratings Grid */}
              <div className="grid grid-cols-3 gap-3 bg-slate-50 p-3 rounded border border-slate-200">
                <div>
                  <label htmlFor="hr-form-tech-rating" className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                    Tech Skills (1-5) *
                  </label>
                  <select
                    id="hr-form-tech-rating"
                    value={hrFormData.technical_skills_rating}
                    onChange={(e) => setHrFormData({ ...hrFormData, technical_skills_rating: Number(e.target.value) })}
                    className="w-full text-sm rounded border border-slate-300 p-1.5 focus:ring-2 focus:ring-gqt-blue"
                  >
                    {[1, 2, 3, 4, 5].map((v) => (
                      <option key={v} value={v}>{v} Star{v > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="hr-form-comm-rating" className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                    Comm Skills (1-5) *
                  </label>
                  <select
                    id="hr-form-comm-rating"
                    value={hrFormData.communication_skills_rating}
                    onChange={(e) => setHrFormData({ ...hrFormData, communication_skills_rating: Number(e.target.value) })}
                    className="w-full text-sm rounded border border-slate-300 p-1.5 focus:ring-2 focus:ring-gqt-blue"
                  >
                    {[1, 2, 3, 4, 5].map((v) => (
                      <option key={v} value={v}>{v} Star{v > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="hr-form-satisfaction-rating" className="block text-[11px] font-bold text-slate-700 uppercase mb-1">
                    Satisfaction (1-5) *
                  </label>
                  <select
                    id="hr-form-satisfaction-rating"
                    value={hrFormData.hiring_satisfaction_rating}
                    onChange={(e) => setHrFormData({ ...hrFormData, hiring_satisfaction_rating: Number(e.target.value) })}
                    className="w-full text-sm rounded border border-slate-300 p-1.5 focus:ring-2 focus:ring-gqt-blue"
                  >
                    {[1, 2, 3, 4, 5].map((v) => (
                      <option key={v} value={v}>{v} Star{v > 1 ? 's' : ''}</option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Remarks */}
              <div>
                <label htmlFor="hr-form-quality-remarks" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Evaluation Remarks
                </label>
                <textarea
                  id="hr-form-quality-remarks"
                  rows={2}
                  placeholder="Key observations on candidate competencies, demeanor, and fit..."
                  value={hrFormData.candidate_quality_remarks}
                  onChange={(e) => setHrFormData({ ...hrFormData, candidate_quality_remarks: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsHRModalOpen(false)}
                  disabled={isActionLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading}
                  className="bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  {isActionLoading ? 'Saving...' : 'Record HR Feedback'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Submit Trainer Feedback */}
      {isTrainerModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden my-8 border border-slate-200">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gqt-navy text-lg">Record Trainer Readiness Feedback</h3>
                <p className="text-xs text-slate-500 mt-0.5">Category C: Student readiness, training effectiveness, areas for improvement</p>
              </div>
              <button
                onClick={() => setIsTrainerModalOpen(false)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleTrainerSubmit} className="p-5 space-y-4">
              {/* Student ID */}
              <div>
                <label htmlFor="trainer-form-student" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Student Profile ID / Roll Number *
                </label>
                <input
                  id="trainer-form-student"
                  type="text"
                  required
                  placeholder="Student UUID or Roll Number"
                  value={trainerFormData.student}
                  onChange={(e) => setTrainerFormData({ ...trainerFormData, student: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Student Readiness */}
              <div>
                <label htmlFor="trainer-form-readiness" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Student Readiness *
                </label>
                <select
                  id="trainer-form-readiness"
                  value={trainerFormData.student_readiness}
                  onChange={(e) => setTrainerFormData({ ...trainerFormData, student_readiness: e.target.value as StudentReadiness })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="HIGHLY_READY">Highly Ready — Strong project portfolio & sharp fundamentals</option>
                  <option value="READY">Ready — Prepared for scheduled corporate drive</option>
                  <option value="NEEDS_PRACTICE">Needs Practice — Requires targeted remediation sessions</option>
                  <option value="NOT_READY">Not Ready — Substantial gaps in core syllabus</option>
                </select>
              </div>

              {/* Training Effectiveness Rating */}
              <div>
                <label htmlFor="trainer-form-effectiveness-rating" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Training Effectiveness (1-5 Stars) *
                </label>
                <select
                  id="trainer-form-effectiveness-rating"
                  value={trainerFormData.training_effectiveness_rating}
                  onChange={(e) => setTrainerFormData({ ...trainerFormData, training_effectiveness_rating: Number(e.target.value) })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                >
                  {[1, 2, 3, 4, 5].map((v) => (
                    <option key={v} value={v}>{v} Star{v > 1 ? 's' : ''}</option>
                  ))}
                </select>
              </div>

              {/* Concrete Areas for Improvement */}
              <div>
                <label htmlFor="trainer-form-improvement-areas" className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Areas for Improvement * (min 10 characters)
                </label>
                <textarea
                  id="trainer-form-improvement-areas"
                  required
                  rows={3}
                  placeholder="Detail actionable technical areas needing practice (e.g., SQL subqueries, async programming)..."
                  value={trainerFormData.areas_for_improvement}
                  onChange={(e) => setTrainerFormData({ ...trainerFormData, areas_for_improvement: e.target.value })}
                  className="w-full text-sm rounded border border-slate-300 p-2 focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsTrainerModalOpen(false)}
                  disabled={isActionLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading}
                  className="bg-gqt-blue hover:bg-blue-700 text-white"
                >
                  {isActionLoading ? 'Saving...' : 'Record Trainer Feedback'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* DETAIL MODAL: View Full Record */}
      {selectedRecord && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden my-8 border border-slate-200">
            <div className="p-5 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-gqt-navy text-lg">{selectedRecord.title}</h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  {selectedRecord.category} • Recorded by {selectedRecord.author} on {selectedRecord.date}
                </p>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-slate-400 hover:text-slate-600 font-bold text-lg"
              >
                ×
              </button>
            </div>

            <div className="p-5 space-y-3 max-h-[70vh] overflow-y-auto">
              {selectedRecord.items.map((item, idx) => (
                <div key={idx} className="border-b border-slate-100 pb-2">
                  <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-0.5">
                    {item.label}
                  </span>
                  <div className="text-sm text-slate-800 whitespace-pre-wrap font-medium">
                    {String(item.value)}
                  </div>
                </div>
              ))}
            </div>

            <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSelectedRecord(null)}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
