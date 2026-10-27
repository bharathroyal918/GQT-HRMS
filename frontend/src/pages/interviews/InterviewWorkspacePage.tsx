import React, { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Users,
  CheckCircle2,
  AlertCircle,
  PhoneCall,
  Video,
  MapPin,
  Bell,
  RefreshCw,
  Plus,
  Search,
  Filter,
  Layers,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge, StatusVariant } from '../../components/common/StatusBadge';
import { interviewsApi } from '../../api/interviewsApi';
import { jobsApi } from '../../api/jobsApi';
import { useAuth } from '../../context/AuthContext';
import {
  CandidateShortlist,
  SubmittableCandidate,
  InterviewSchedule,
  InterviewRound,
  HRInterviewFollowUp,
  InterviewKPIs,
  RoundCategory,
  AttendanceStatus,
  ConductedStatus,
} from '../../types/interviews';
import { JobRequirementListItem } from '../../types/jobs';

export const InterviewWorkspacePage: React.FC = () => {
  const { hasAnyRole } = useAuth();
  const isStaff = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR']);

  // Active Tab: 'schedules' | 'shortlists' | 'rounds' | 'followups'
  const [activeTab, setActiveTab] = useState<'schedules' | 'shortlists' | 'rounds' | 'followups'>('schedules');

  // Loading & Error States
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isActionLoading, setIsActionLoading] = useState(false);

  // Data States
  const [kpis, setKpis] = useState<InterviewKPIs | null>(null);
  const [schedules, setSchedules] = useState<InterviewSchedule[]>([]);
  const [shortlists, setShortlists] = useState<CandidateShortlist[]>([]);
  const [rounds, setRounds] = useState<InterviewRound[]>([]);
  const [followUps, setFollowUps] = useState<HRInterviewFollowUp[]>([]);
  const [approvedJobs, setApprovedJobs] = useState<JobRequirementListItem[]>([]);

  // Filter States
  const [selectedJobFilter, setSelectedJobFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Modals
  const [isShortlistModalOpen, setIsShortlistModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [isAttendanceModalOpen, setIsAttendanceModalOpen] = useState(false);
  const [isConductedModalOpen, setIsConductedModalOpen] = useState(false);
  const [isRoundModalOpen, setIsRoundModalOpen] = useState(false);
  const [isEvaluateRoundModalOpen, setIsEvaluateRoundModalOpen] = useState(false);
  const [isFollowUpModalOpen, setIsFollowUpModalOpen] = useState(false);
  const [isRemindersModalOpen, setIsRemindersModalOpen] = useState(false);

  // Selected Items for Modals
  const [activeSchedule, setActiveSchedule] = useState<InterviewSchedule | null>(null);
  const [activeRound, setActiveRound] = useState<InterviewRound | null>(null);

  // Shortlist Modal Form
  const [modalJobId, setModalJobId] = useState<string>('');
  const [submittableCandidates, setSubmittableCandidates] = useState<SubmittableCandidate[]>([]);
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [shortlistSource, setShortlistSource] = useState<'EMAIL' | 'PORTAL' | 'FILE_IMPORT' | 'DIRECT_HANDOFF'>('EMAIL');
  const [shortlistNotes, setShortlistNotes] = useState<string>('');
  const [isLoadingSubmittables, setIsLoadingSubmittables] = useState(false);

  // Schedule Modal Form
  const [scheduleCandidateId, setScheduleCandidateId] = useState<string>('');
  const [scheduleDate, setScheduleDate] = useState<string>('');
  const [scheduleTime, setScheduleTime] = useState<string>('10:00');
  const [scheduleMode, setScheduleMode] = useState<'ONLINE' | 'IN_PERSON' | 'HYBRID'>('ONLINE');
  const [scheduleVenue, setScheduleVenue] = useState<string>('');
  const [scheduleLink, setScheduleLink] = useState<string>('');
  const [scheduleDocs, setScheduleDocs] = useState<string>(
    'Resume copies (2), Government Photo ID, College ID, Academic Marksheets (original + photocopy)'
  );

  // Attendance Modal Form
  const [attendanceChoice, setAttendanceChoice] = useState<AttendanceStatus>('CONFIRMED');
  const [attendanceNotes, setAttendanceNotes] = useState<string>('');

  // Conducted Modal Form
  const [conductedChoice, setConductedChoice] = useState<ConductedStatus>('CONDUCTED');
  const [conductedNotes, setConductedNotes] = useState<string>('');

  // Round Modal Form
  const [roundCategory, setRoundCategory] = useState<RoundCategory>('TECHNICAL');
  const [roundName, setRoundName] = useState<string>('');
  const [roundInterviewer, setRoundInterviewer] = useState<string>('');
  const [roundDate, setRoundDate] = useState<string>('');
  const [roundTime, setRoundTime] = useState<string>('');
  const [roundNotes, setRoundNotes] = useState<string>('');

  // Evaluate Round Form
  const [evalRoundStatus, setEvalRoundStatus] = useState<'CLEARED' | 'NOT_CLEARED' | 'ON_HOLD'>('CLEARED');
  const [evalRoundNotes, setEvalRoundNotes] = useState<string>('');

  // Follow-up Modal Form
  const [followUpJobId, setFollowUpJobId] = useState<string>('');
  const [candidateStatusReported, setCandidateStatusReported] = useState<string>('');
  const [pendingRoundsText, setPendingRoundsText] = useState<string>('');
  const [expectedResultDate, setExpectedResultDate] = useState<string>('');
  const [isDateConfirmed, setIsDateConfirmed] = useState<boolean>(true);
  const [nextFollowUpDate, setNextFollowUpDate] = useState<string>('');
  const [followUpSummary, setFollowUpSummary] = useState<string>('');

  // Fetch primary workspace data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isStaff) {
        const [kpiRes, schedRes, shortRes, roundRes, fuRes, jobsRes] = await Promise.all([
          interviewsApi.getKPIs(),
          interviewsApi.listSchedules({
            job_id: selectedJobFilter || undefined,
            search: searchQuery || undefined,
          }),
          interviewsApi.listShortlists({
            job_id: selectedJobFilter || undefined,
            search: searchQuery || undefined,
          }),
          interviewsApi.listRounds({
            job_id: selectedJobFilter || undefined,
          }),
          interviewsApi.listFollowUps({
            job_id: selectedJobFilter || undefined,
            search: searchQuery || undefined,
          }),
          jobsApi.getJobs({ status: 'APPROVED' }),
        ]);

        setKpis(kpiRes);
        setSchedules(schedRes);
        setShortlists(shortRes);
        setRounds(roundRes);
        setFollowUps(fuRes);
        setApprovedJobs(jobsRes.data || []);
      } else {
        // Student View
        const studentSchedules = await interviewsApi.getMyInterviews();
        setSchedules(studentSchedules);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load interview workspace records.');
    } finally {
      setIsLoading(false);
    }
  }, [isStaff, selectedJobFilter, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Load submittable candidates when job is picked in Shortlist modal
  useEffect(() => {
    if (!modalJobId) {
      setSubmittableCandidates([]);
      setSelectedStudentIds([]);
      return;
    }
    const loadSubmittables = async () => {
      setIsLoadingSubmittables(true);
      try {
        const candidates = await interviewsApi.getSubmittableCandidates(modalJobId);
        setSubmittableCandidates(candidates);
      } catch (err: any) {
        setError(err?.response?.data?.detail || 'Failed to load submittable candidates for job.');
      } finally {
        setIsLoadingSubmittables(false);
      }
    };
    loadSubmittables();
  }, [modalJobId]);

  // Action: Trigger Automatic Reminders (Step 31)
  const handleProcessReminders = async () => {
    setIsActionLoading(true);
    setActionSuccess(null);
    try {
      const res = await interviewsApi.processDueReminders();
      setActionSuccess(res.message);
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to process reminders.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Create Shortlist (Step 29)
  const handleCreateShortlist = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!modalJobId || selectedStudentIds.length === 0) return;
    const selectedJob = approvedJobs.find((j) => j.id === modalJobId);
    if (!selectedJob || !selectedJob.hr_contact) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.createShortlist({
        job_id: modalJobId,
        company_id: selectedJob.company,
        hr_contact_id: selectedJob.hr_contact,
        student_ids: selectedStudentIds,
        source: shortlistSource,
        notes: shortlistNotes,
      });
      setActionSuccess('Candidate shortlist successfully recorded.');
      setIsShortlistModalOpen(false);
      setModalJobId('');
      setSelectedStudentIds([]);
      setShortlistNotes('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to record candidate shortlist.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Schedule Interview (Step 30)
  const handleCreateSchedule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scheduleCandidateId || !scheduleDate || !scheduleTime) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.createSchedule({
        candidate_id: scheduleCandidateId,
        interview_date: scheduleDate,
        interview_time: scheduleTime,
        mode: scheduleMode,
        venue: scheduleVenue,
        meeting_link: scheduleLink,
        required_documents: scheduleDocs,
      });
      setActionSuccess('Interview scheduled and automatic reminders initialized.');
      setIsScheduleModalOpen(false);
      setScheduleCandidateId('');
      setScheduleVenue('');
      setScheduleLink('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to schedule interview.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Notify Student (Step 30)
  const handleNotifyStudent = async (scheduleId: string) => {
    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.notifyStudent(scheduleId, 'EMAIL');
      setActionSuccess('Interview notification dispatched to candidate.');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to dispatch student notification.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Confirm Attendance (Step 32)
  const handleConfirmAttendance = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSchedule) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.confirmAttendance(activeSchedule.id, {
        attendance_status: attendanceChoice as any,
        notes: attendanceNotes,
      });
      setActionSuccess('Attendance confirmation recorded.');
      setIsAttendanceModalOpen(false);
      setActiveSchedule(null);
      setAttendanceNotes('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to confirm attendance.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Mark Conducted (Step 33)
  const handleRecordConducted = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSchedule) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.recordConducted(activeSchedule.id, {
        conducted_status: conductedChoice,
        notes: conductedNotes,
      });
      setActionSuccess('Interview conducted outcome recorded.');
      setIsConductedModalOpen(false);
      setActiveSchedule(null);
      setConductedNotes('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to record conducted outcome.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Create Round (Step 34)
  const handleCreateRound = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSchedule) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.createRound({
        candidate_id: activeSchedule.candidate,
        category: roundCategory,
        round_name: roundName,
        interviewer_names: roundInterviewer,
        scheduled_date: roundDate || null,
        scheduled_time: roundTime || null,
        internal_staff_notes: roundNotes,
        schedule_id: activeSchedule.id,
      });
      setActionSuccess('Interview round created.');
      setIsRoundModalOpen(false);
      setActiveSchedule(null);
      setRoundName('');
      setRoundInterviewer('');
      setRoundDate('');
      setRoundTime('');
      setRoundNotes('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to create interview round.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Evaluate Round (Step 34)
  const handleEvaluateRound = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeRound) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.evaluateRound(activeRound.id, {
        status: evalRoundStatus,
        internal_staff_notes: evalRoundNotes,
      });
      setActionSuccess(`Round marked as ${evalRoundStatus}.`);
      setIsEvaluateRoundModalOpen(false);
      setActiveRound(null);
      setEvalRoundNotes('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to evaluate interview round.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Action: Record HR Follow-up (Step 35)
  const handleRecordFollowUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!followUpJobId || !candidateStatusReported) return;
    const selectedJob = approvedJobs.find((j) => j.id === followUpJobId);
    if (!selectedJob || !selectedJob.hr_contact) return;

    setIsActionLoading(true);
    setError(null);
    try {
      await interviewsApi.createFollowUp({
        job_id: followUpJobId,
        company_id: selectedJob.company,
        hr_contact_id: selectedJob.hr_contact,
        candidate_status_reported: candidateStatusReported,
        pending_rounds: pendingRoundsText,
        expected_result_date: expectedResultDate || null,
        is_date_confirmed: isDateConfirmed,
        next_follow_up_date: nextFollowUpDate || null,
        hr_response_summary: followUpSummary,
      });
      setActionSuccess('Corporate HR follow-up touchpoint recorded.');
      setIsFollowUpModalOpen(false);
      setFollowUpJobId('');
      setCandidateStatusReported('');
      setPendingRoundsText('');
      setExpectedResultDate('');
      setNextFollowUpDate('');
      setFollowUpSummary('');
      await fetchData();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to record HR follow-up.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Helper for status badge variant
  const getStatusVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'SCHEDULED':
      case 'CONFIRMED':
      case 'CONDUCTED':
      case 'CLEARED':
      case 'SENT':
        return 'success';
      case 'IN_PROGRESS':
      case 'TENTATIVE':
      case 'PROCESSING':
      case 'RESPONSE_RECEIVED':
        return 'info';
      case 'NO_RESPONSE':
      case 'PENDING':
      case 'ON_HOLD':
      case 'SKIPPED':
      case 'AWAITING_RESPONSE':
        return 'warning';
      case 'DECLINED':
      case 'NOT_CONDUCTED':
      case 'CANDIDATE_ABSENT':
      case 'NOT_CLEARED':
      case 'CANCELLED':
      case 'FAILED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#1B365D]">
            Interview Management & Tracking
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Authoritative workflow steps 29–35: Shortlists, scheduling, notifications, reminders, attendance, and round tracking.
          </p>
        </div>

        {isStaff && (
          <div className="flex flex-wrap items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleProcessReminders}
              isLoading={isActionLoading}
              leftIcon={<Bell className="h-4 w-4 text-blue-600" />}
              data-testid="process-reminders-button"
            >
              Trigger Due Reminders
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsShortlistModalOpen(true)}
              leftIcon={<Plus className="h-4 w-4" />}
              data-testid="intake-shortlist-button"
            >
              Intake HR Shortlist
            </Button>
          </div>
        )}
      </div>

      {/* Notifications / Alerts */}
      {actionSuccess && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm">
          <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
          <span>{actionSuccess}</span>
          <button
            onClick={() => setActionSuccess(null)}
            className="ml-auto text-emerald-600 hover:text-emerald-800 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 text-red-800 rounded-lg text-sm">
          <AlertCircle className="h-4 w-4 text-red-600 flex-shrink-0" />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-600 hover:text-red-800 text-xs font-semibold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Cards (Staff View) */}
      {isStaff && kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <Card className="p-4 border-l-4 border-l-blue-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Shortlists</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{kpis.total_shortlists}</p>
            <p className="text-xs text-gray-500 mt-0.5">{kpis.total_shortlisted_candidates} Candidates</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-indigo-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">{kpis.total_schedules}</p>
            <p className="text-xs text-indigo-600 mt-0.5">Active Sessions</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-emerald-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Attendance</p>
            <p className="text-2xl font-bold text-emerald-700 mt-1">{kpis.confirmed_attendance}</p>
            <p className="text-xs text-emerald-600 mt-0.5">Confirmed Ready</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-amber-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Conducted</p>
            <p className="text-2xl font-bold text-amber-700 mt-1">{kpis.interviews_conducted}</p>
            <p className="text-xs text-amber-600 mt-0.5">Completed Sessions</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-purple-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Rounds Logged</p>
            <p className="text-2xl font-bold text-purple-700 mt-1">{rounds.length}</p>
            <p className="text-xs text-purple-600 mt-0.5">Apt/Tech/HR/Mgr</p>
          </Card>
          <Card className="p-4 border-l-4 border-l-cyan-600 shadow-xs">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">HR Follow-ups</p>
            <p className="text-2xl font-bold text-cyan-700 mt-1">{kpis.pending_hr_followups}</p>
            <p className="text-xs text-cyan-600 mt-0.5">Scheduled Callbacks</p>
          </Card>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex border-b border-gray-200">
        <button
          onClick={() => setActiveTab('schedules')}
          className={`py-3 px-5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
            activeTab === 'schedules'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-700'
          }`}
          data-testid="tab-schedules"
        >
          <Calendar className="h-4 w-4" />
          Schedules & Notifications (Steps 30–33)
        </button>

        {isStaff && (
          <>
            <button
              onClick={() => setActiveTab('shortlists')}
              className={`py-3 px-5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'shortlists'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-shortlists"
            >
              <Users className="h-4 w-4" />
              Shortlists Received (Step 29)
            </button>

            <button
              onClick={() => setActiveTab('rounds')}
              className={`py-3 px-5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'rounds'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-rounds"
            >
              <Layers className="h-4 w-4" />
              Interview Rounds (Step 34)
            </button>

            <button
              onClick={() => setActiveTab('followups')}
              className={`py-3 px-5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'followups'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
              data-testid="tab-followups"
            >
              <PhoneCall className="h-4 w-4" />
              HR Follow-ups (Step 35)
            </button>
          </>
        )}
      </div>

      {/* Filter Bar (Staff Only) */}
      {isStaff && (
        <div className="flex flex-wrap items-center gap-4 bg-gray-50 p-3 rounded-lg border border-gray-200 text-sm">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="font-medium text-gray-700">Filter by Job:</span>
            <select
              value={selectedJobFilter}
              onChange={(e) => setSelectedJobFilter(e.target.value)}
              className="border border-gray-300 rounded-md px-2.5 py-1 text-sm bg-white"
            >
              <option value="">All Approved Jobs</option>
              {approvedJobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.company_name} — {j.title}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <Search className="h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search reference, roll, or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="border border-gray-300 rounded-md px-2.5 py-1 text-sm bg-white w-64"
            />
          </div>
        </div>
      )}

      {/* TAB CONTENT: Schedules & Notifications */}
      {activeTab === 'schedules' && (
        <Card className="overflow-hidden shadow-xs">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">
              {isStaff ? 'Interview Schedules & Delivery Tracking' : 'My Scheduled Interviews'}
            </h2>
            {isStaff && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsScheduleModalOpen(true)}
                leftIcon={<Plus className="h-4 w-4" />}
                data-testid="schedule-interview-button"
              >
                Schedule Candidate
              </Button>
            )}
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Schedule Code</th>
                  <th className="px-4 py-3">Candidate</th>
                  <th className="px-4 py-3">Company & Job</th>
                  <th className="px-4 py-3">Date & Time</th>
                  <th className="px-4 py-3">Mode & Link/Venue</th>
                  <th className="px-4 py-3">Notification (Step 30)</th>
                  <th className="px-4 py-3">Attendance (Step 32)</th>
                  <th className="px-4 py-3">Conducted (Step 33)</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {isLoading ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                      <RefreshCw className="h-6 w-6 animate-spin mx-auto text-blue-600 mb-2" />
                      Loading interview schedules...
                    </td>
                  </tr>
                ) : schedules.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                      No interview schedules found.
                    </td>
                  </tr>
                ) : (
                  schedules.map((sch) => (
                    <tr key={sch.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3 font-mono text-xs font-semibold text-[#1B365D]">
                        {sch.schedule_reference_code}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{sch.candidate_name}</div>
                        <div className="text-xs text-gray-500 font-mono">{sch.candidate_roll}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{sch.company_name}</div>
                        <div className="text-xs text-gray-500">{sch.job_title}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{sch.interview_date}</div>
                        <div className="text-xs text-gray-500">{sch.interview_time}</div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          {sch.mode === 'ONLINE' ? (
                            <Video className="h-4 w-4 text-blue-600 flex-shrink-0" />
                          ) : (
                            <MapPin className="h-4 w-4 text-emerald-600 flex-shrink-0" />
                          )}
                          <span className="font-medium text-xs text-gray-800">{sch.mode_display}</span>
                        </div>
                        {sch.meeting_link && (
                          <a
                            href={sch.meeting_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline block truncate max-w-[140px]"
                          >
                            Meeting Link
                          </a>
                        )}
                        {sch.venue && <div className="text-xs text-gray-500 truncate max-w-[140px]">{sch.venue}</div>}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge
                          label={sch.notification_status}
                          variant={sch.notification_status === 'SENT' ? 'success' : 'neutral'}
                        />
                        <button
                          onClick={() => {
                            setActiveSchedule(sch);
                            setIsRemindersModalOpen(true);
                          }}
                          className="block text-xs text-blue-600 hover:underline mt-1 font-medium"
                          data-testid={`reminders-btn-${sch.id}`}
                        >
                          View 3 Reminders
                        </button>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge
                          label={sch.attendance_status_display}
                          variant={getStatusVariant(sch.attendance_status)}
                        />
                        <div className="text-xs text-gray-500 mt-0.5">{sch.attendance_source}</div>
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge
                          label={sch.conducted_status_display}
                          variant={getStatusVariant(sch.conducted_status)}
                        />
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Student Attendance Self-Confirmation */}
                          {(!isStaff || sch.attendance_status === 'NO_RESPONSE') && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setActiveSchedule(sch);
                                setIsAttendanceModalOpen(true);
                              }}
                              data-testid={`confirm-attendance-btn-${sch.id}`}
                            >
                              Attendance
                            </Button>
                          )}

                          {/* Staff-only actions */}
                          {isStaff && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleNotifyStudent(sch.id)}
                                isLoading={isActionLoading}
                                title="Step 30: Dispatch student notification"
                                data-testid={`notify-btn-${sch.id}`}
                              >
                                Notify
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setActiveSchedule(sch);
                                  setIsConductedModalOpen(true);
                                }}
                                title="Step 33: Record interview conducted"
                                data-testid={`conducted-btn-${sch.id}`}
                              >
                                Conducted
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setActiveSchedule(sch);
                                  setIsRoundModalOpen(true);
                                }}
                                title="Step 34: Add interview round"
                                data-testid={`add-round-btn-${sch.id}`}
                              >
                                + Round
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB CONTENT: Shortlists (Step 29) */}
      {activeTab === 'shortlists' && isStaff && (
        <Card className="overflow-hidden shadow-xs">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-base font-semibold text-gray-900">Corporate Shortlists Ingested (Step 29)</h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsShortlistModalOpen(true)}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Intake New Shortlist
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Reference Code</th>
                  <th className="px-4 py-3">Company & Job</th>
                  <th className="px-4 py-3">HR Contact</th>
                  <th className="px-4 py-3">Candidates</th>
                  <th className="px-4 py-3">Source</th>
                  <th className="px-4 py-3">Date Received</th>
                  <th className="px-4 py-3">Recorded By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {shortlists.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-gray-500">
                      No corporate shortlists recorded.
                    </td>
                  </tr>
                ) : (
                  shortlists.map((sl) => (
                    <tr key={sl.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3 font-mono font-semibold text-[#1B365D]">
                        {sl.shortlist_reference_code}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{sl.company_name}</div>
                        <div className="text-xs text-gray-500">{sl.job_title}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{sl.hr_contact_name}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800">
                          {sl.candidate_count} Shortlisted
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">{sl.source}</td>
                      <td className="px-4 py-3 text-gray-600">{new Date(sl.received_at).toLocaleDateString()}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{sl.created_by_name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB CONTENT: Interview Rounds (Step 34) */}
      {activeTab === 'rounds' && isStaff && (
        <Card className="overflow-hidden shadow-xs">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Candidate Interview Rounds (Step 34)</h2>
              <p className="text-xs text-gray-500">
                Authoritative categories: Aptitude, Coding, Technical, HR, Managerial.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Candidate</th>
                  <th className="px-4 py-3">Round #</th>
                  <th className="px-4 py-3">Category</th>
                  <th className="px-4 py-3">Round Title</th>
                  <th className="px-4 py-3">Interviewer</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Evaluator</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {rounds.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                      No interview rounds recorded.
                    </td>
                  </tr>
                ) : (
                  rounds.map((rnd) => (
                    <tr key={rnd.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{rnd.candidate_name}</div>
                        <div className="text-xs text-gray-500 font-mono">{rnd.candidate_roll}</div>
                      </td>
                      <td className="px-4 py-3 font-semibold text-gray-900">Round {rnd.round_number}</td>
                      <td className="px-4 py-3">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800">
                          {rnd.category_display}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-800">{rnd.round_name}</td>
                      <td className="px-4 py-3 text-xs text-gray-600">{rnd.interviewer_names || 'TBD'}</td>
                      <td className="px-4 py-3">
                        <StatusBadge label={rnd.status_display} variant={getStatusVariant(rnd.status)} />
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500">{rnd.evaluated_by_name || 'Pending'}</td>
                      <td className="px-4 py-3 text-right">
                        {rnd.status === 'SCHEDULED' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setActiveRound(rnd);
                              setIsEvaluateRoundModalOpen(true);
                            }}
                            data-testid={`eval-round-btn-${rnd.id}`}
                          >
                            Evaluate
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* TAB CONTENT: HR Follow-ups (Step 35) */}
      {activeTab === 'followups' && isStaff && (
        <Card className="overflow-hidden shadow-xs">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Corporate HR Follow-ups (Step 35)</h2>
              <p className="text-xs text-gray-500">
                Authoritative metrics: Candidate status, pending rounds, and expected result date.
              </p>
            </div>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsFollowUpModalOpen(true)}
              leftIcon={<Plus className="h-4 w-4" />}
              data-testid="log-followup-button"
            >
              Log HR Follow-up
            </Button>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm text-left">
              <thead className="bg-gray-50 text-gray-600 font-medium">
                <tr>
                  <th className="px-4 py-3">Company & Job</th>
                  <th className="px-4 py-3">HR Contact</th>
                  <th className="px-4 py-3">Reported Candidate Status</th>
                  <th className="px-4 py-3">Pending Rounds</th>
                  <th className="px-4 py-3">Expected Result Date</th>
                  <th className="px-4 py-3">Next Callback</th>
                  <th className="px-4 py-3">Channel</th>
                  <th className="px-4 py-3">Conducted By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {followUps.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                      No HR follow-ups recorded.
                    </td>
                  </tr>
                ) : (
                  followUps.map((fu) => (
                    <tr key={fu.id} className="hover:bg-gray-50/50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">{fu.company_name}</div>
                        <div className="text-xs text-gray-500">{fu.job_title}</div>
                      </td>
                      <td className="px-4 py-3 text-gray-700">{fu.hr_contact_name}</td>
                      <td className="px-4 py-3 font-medium text-blue-900">{fu.candidate_status_reported}</td>
                      <td className="px-4 py-3 text-xs text-gray-600">{fu.pending_rounds || 'None'}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-gray-900">
                          {fu.expected_result_date ? fu.expected_result_date : 'Not Specified'}
                        </div>
                        <div className="text-xs text-gray-500">
                          {fu.is_date_confirmed ? 'Confirmed Firm' : 'Tentative Estimate'}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-xs font-semibold text-amber-700">
                          {fu.next_follow_up_date || 'N/A'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-600">{fu.channel_display}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{fu.conducted_by_name}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* ======================================================================
          MODAL: Intake HR Shortlist (Step 29)
      ====================================================================== */}
      {isShortlistModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Receive Candidate Shortlist (Step 29)</h3>
              <button
                onClick={() => setIsShortlistModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateShortlist} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Approved Job Requirement *
                </label>
                <select
                  value={modalJobId}
                  onChange={(e) => setModalJobId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  required
                  data-testid="shortlist-job-select"
                >
                  <option value="">Select an approved job requirement...</option>
                  {approvedJobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.company_name} — {j.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Submittable Candidates Checkboxes */}
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Select Candidates from Submitted Pool ({selectedStudentIds.length} selected) *
                </label>

                {isLoadingSubmittables ? (
                  <div className="p-4 text-center text-sm text-gray-500">
                    <RefreshCw className="h-4 w-4 animate-spin mx-auto text-blue-600 mb-1" />
                    Loading submitted candidates...
                  </div>
                ) : submittableCandidates.length === 0 ? (
                  <div className="p-4 bg-gray-50 border rounded-md text-xs text-gray-500 text-center">
                    {modalJobId
                      ? 'No submitted candidates found for this job. Ensure profiles were dispatched in Phase 7.'
                      : 'Please select a job above to view submitted candidates.'}
                  </div>
                ) : (
                  <div className="border rounded-md divide-y max-h-56 overflow-y-auto">
                    {submittableCandidates.map((c) => (
                      <label
                        key={c.student_id}
                        className={`flex items-center gap-3 p-2.5 text-xs hover:bg-gray-50 cursor-pointer ${
                          c.is_already_shortlisted ? 'opacity-50 cursor-not-allowed bg-gray-50' : ''
                        }`}
                      >
                        <input
                          type="checkbox"
                          disabled={c.is_already_shortlisted}
                          checked={selectedStudentIds.includes(c.student_id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedStudentIds([...selectedStudentIds, c.student_id]);
                            } else {
                              setSelectedStudentIds(selectedStudentIds.filter((id) => id !== c.student_id));
                            }
                          }}
                          className="rounded text-blue-600"
                        />
                        <div className="flex-1">
                          <span className="font-bold text-gray-900">{c.full_name}</span> ({c.roll_number})
                          <div className="text-gray-500">
                            {c.degree} {c.department} • CGPA: {c.cgpa}
                          </div>
                        </div>
                        {c.is_already_shortlisted && (
                          <span className="text-[10px] font-semibold bg-gray-200 text-gray-700 px-2 py-0.5 rounded">
                            Already Shortlisted
                          </span>
                        )}
                      </label>
                    ))}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Intake Source
                  </label>
                  <select
                    value={shortlistSource}
                    onChange={(e: any) => setShortlistSource(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  >
                    <option value="EMAIL">Corporate Email</option>
                    <option value="PORTAL">Recruiter Portal Export</option>
                    <option value="FILE_IMPORT">Spreadsheet Import</option>
                    <option value="DIRECT_HANDOFF">Direct Handoff / Meeting</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Recruiter Remarks / Notes
                </label>
                <textarea
                  value={shortlistNotes}
                  onChange={(e) => setShortlistNotes(e.target.value)}
                  placeholder="e.g. Selected candidates for Aptitude and Coding rounds..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsShortlistModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isActionLoading}
                  disabled={selectedStudentIds.length === 0}
                  data-testid="submit-shortlist-btn"
                >
                  Record Shortlist
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Schedule Candidate Interview (Step 30 & 31)
      ====================================================================== */}
      {isScheduleModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Schedule Interview (Step 30)</h3>
              <button onClick={() => setIsScheduleModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateSchedule} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Shortlisted Candidate *
                </label>
                <select
                  value={scheduleCandidateId}
                  onChange={(e) => setScheduleCandidateId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  required
                  data-testid="schedule-candidate-select"
                >
                  <option value="">Select shortlisted candidate...</option>
                  {shortlists.flatMap((sl) =>
                    sl.candidates.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.full_name} ({c.roll_number}) — {sl.company_name}
                      </option>
                    ))
                  )}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Date *
                  </label>
                  <input
                    type="date"
                    value={scheduleDate}
                    onChange={(e) => setScheduleDate(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    required
                    data-testid="schedule-date-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Time *
                  </label>
                  <input
                    type="time"
                    value={scheduleTime}
                    onChange={(e) => setScheduleTime(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    required
                    data-testid="schedule-time-input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Interview Mode *
                </label>
                <select
                  value={scheduleMode}
                  onChange={(e: any) => setScheduleMode(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                >
                  <option value="ONLINE">Virtual / Online (Teams / Zoom)</option>
                  <option value="IN_PERSON">In-Person (Campus / Corporate Office)</option>
                  <option value="HYBRID">Hybrid</option>
                </select>
              </div>

              {scheduleMode !== 'IN_PERSON' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Meeting Link *
                  </label>
                  <input
                    type="url"
                    placeholder="https://teams.microsoft.com/..."
                    value={scheduleLink}
                    onChange={(e) => setScheduleLink(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    required={scheduleMode === 'ONLINE'}
                  />
                </div>
              )}

              {scheduleMode !== 'ONLINE' && (
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Venue / Room *
                  </label>
                  <input
                    type="text"
                    placeholder="Seminar Hall 2, Placement Block"
                    value={scheduleVenue}
                    onChange={(e) => setScheduleVenue(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    required={scheduleMode === 'IN_PERSON'}
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Required Documents (Authoritative Step 30 field)
                </label>
                <textarea
                  value={scheduleDocs}
                  onChange={(e) => setScheduleDocs(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-md text-xs text-blue-900 flex items-center gap-2">
                <Bell className="h-4 w-4 text-blue-600 flex-shrink-0" />
                <span>
                  Automatic reminders at <strong>24h</strong>, <strong>2h</strong>, and <strong>30m</strong> will be scheduled automatically (Step 31).
                </span>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsScheduleModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" isLoading={isActionLoading}>
                  Confirm Schedule
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Confirm Attendance (Step 32)
      ====================================================================== */}
      {isAttendanceModalOpen && activeSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Confirm Attendance (Step 32)</h3>
              <button onClick={() => setIsAttendanceModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleConfirmAttendance} className="space-y-4">
              <p className="text-sm text-gray-600">
                Recording attendance response for <strong>{activeSchedule.candidate_name}</strong> (
                {activeSchedule.candidate_roll}) scheduled on <strong>{activeSchedule.interview_date}</strong> at{' '}
                <strong>{activeSchedule.interview_time}</strong>.
              </p>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Attendance Response *
                </label>
                <select
                  value={attendanceChoice}
                  onChange={(e: any) => setAttendanceChoice(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  data-testid="attendance-choice-select"
                >
                  <option value="CONFIRMED">Confirmed / Attending</option>
                  <option value="DECLINED">Declined / Cannot Attend</option>
                  <option value="TENTATIVE">Tentative / Clarification Requested</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Reason / Notes
                </label>
                <textarea
                  value={attendanceNotes}
                  onChange={(e) => setAttendanceNotes(e.target.value)}
                  placeholder="Optional notes or reason if declining..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsAttendanceModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isActionLoading}
                  data-testid="save-attendance-btn"
                >
                  Save Attendance
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Record Interview Conducted (Step 33)
      ====================================================================== */}
      {isConductedModalOpen && activeSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Record Interview Conducted (Step 33)</h3>
              <button onClick={() => setIsConductedModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordConducted} className="space-y-4">
              <p className="text-sm text-gray-600">
                Record whether the scheduled session for <strong>{activeSchedule.candidate_name}</strong> was conducted.
              </p>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Conducted Status *
                </label>
                <select
                  value={conductedChoice}
                  onChange={(e: any) => setConductedChoice(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  data-testid="conducted-choice-select"
                >
                  <option value="CONDUCTED">Interview Conducted</option>
                  <option value="NOT_CONDUCTED">Not Conducted</option>
                  <option value="CANDIDATE_ABSENT">Candidate Absent</option>
                  <option value="INTERVIEWER_ABSENT">Interviewer Unavailable</option>
                  <option value="RESCHEDULED">Session Rescheduled</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Operational Remarks
                </label>
                <textarea
                  value={conductedNotes}
                  onChange={(e) => setConductedNotes(e.target.value)}
                  placeholder="Observations from the interview drive..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsConductedModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isActionLoading}
                  data-testid="save-conducted-btn"
                >
                  Save Outcome
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: View 3 Authoritative Reminders (Step 31)
      ====================================================================== */}
      {isRemindersModalOpen && activeSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">
                Automatic Reminders (Step 31)
              </h3>
              <button onClick={() => setIsRemindersModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-gray-600">
                Authoritative reminder intervals configured for Schedule <strong>{activeSchedule.schedule_reference_code}</strong>:
              </p>

              <div className="space-y-2">
                {activeSchedule.reminders && activeSchedule.reminders.length > 0 ? (
                  activeSchedule.reminders.map((rem) => (
                    <div
                      key={rem.id}
                      className="flex items-center justify-between p-3 bg-gray-50 border rounded-lg text-xs"
                    >
                      <div>
                        <div className="font-semibold text-gray-900">{rem.interval_display}</div>
                        <div className="text-gray-500">{new Date(rem.scheduled_for).toLocaleString()}</div>
                      </div>
                      <div className="text-right">
                        <StatusBadge label={rem.status_display} variant={getStatusVariant(rem.status)} />
                        {rem.provider_message_id && (
                          <div className="font-mono text-[10px] text-gray-400 mt-0.5">
                            {rem.provider_message_id}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-gray-500">No reminders registered for this schedule.</p>
                )}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t">
              <Button variant="outline" size="sm" onClick={() => setIsRemindersModalOpen(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Add Interview Round (Step 34)
      ====================================================================== */}
      {isRoundModalOpen && activeSchedule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Add Interview Round (Step 34)</h3>
              <button onClick={() => setIsRoundModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRound} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Round Category *
                </label>
                <select
                  value={roundCategory}
                  onChange={(e: any) => setRoundCategory(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  data-testid="round-category-select"
                >
                  <option value="APTITUDE">Aptitude Round</option>
                  <option value="CODING">Coding / Technical Assessment</option>
                  <option value="TECHNICAL">Technical Interview</option>
                  <option value="HR">HR Interview</option>
                  <option value="MANAGERIAL">Managerial / Leadership Round</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Round Label
                </label>
                <input
                  type="text"
                  placeholder="e.g. Round 2: Data Structures & Algorithms"
                  value={roundName}
                  onChange={(e) => setRoundName(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Scheduled Date
                  </label>
                  <input
                    type="date"
                    value={roundDate}
                    onChange={(e) => setRoundDate(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    data-testid="round-date-input"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Scheduled Time
                  </label>
                  <input
                    type="time"
                    value={roundTime}
                    onChange={(e) => setRoundTime(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                    data-testid="round-time-input"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Interviewer Panel
                </label>
                <input
                  type="text"
                  placeholder="e.g. Lead Architect + Senior Engineer"
                  value={roundInterviewer}
                  onChange={(e) => setRoundInterviewer(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Confidential Staff Notes (Stripped from student view)
                </label>
                <textarea
                  value={roundNotes}
                  onChange={(e) => setRoundNotes(e.target.value)}
                  placeholder="Internal evaluation expectations..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsRoundModalOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" size="sm" type="submit" isLoading={isActionLoading}>
                  Create Round
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Evaluate Interview Round (Step 34)
      ====================================================================== */}
      {isEvaluateRoundModalOpen && activeRound && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Evaluate Round (Step 34)</h3>
              <button
                onClick={() => setIsEvaluateRoundModalOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEvaluateRound} className="space-y-4">
              <p className="text-sm text-gray-600">
                Evaluating Round {activeRound.round_number} ({activeRound.category_display}) for{' '}
                <strong>{activeRound.candidate_name}</strong>.
              </p>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Evaluation Outcome *
                </label>
                <select
                  value={evalRoundStatus}
                  onChange={(e: any) => setEvalRoundStatus(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  data-testid="eval-round-status-select"
                >
                  <option value="CLEARED">Cleared / Advance to Next Round</option>
                  <option value="NOT_CLEARED">Not Cleared / Eliminated</option>
                  <option value="ON_HOLD">On Hold / Decision Awaited</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Confidential Staff Remarks
                </label>
                <textarea
                  value={evalRoundNotes}
                  onChange={(e) => setEvalRoundNotes(e.target.value)}
                  placeholder="Interviewer scorecard notes..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsEvaluateRoundModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isActionLoading}
                  data-testid="save-round-eval-btn"
                >
                  Submit Evaluation
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ======================================================================
          MODAL: Log Corporate HR Follow-up (Step 35)
      ====================================================================== */}
      {isFollowUpModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-lg font-bold text-[#1B365D]">Log HR Follow-up (Step 35)</h3>
              <button onClick={() => setIsFollowUpModalOpen(false)} className="text-gray-400 hover:text-gray-600">
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordFollowUp} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Job Requirement *
                </label>
                <select
                  value={followUpJobId}
                  onChange={(e) => setFollowUpJobId(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm bg-white"
                  required
                  data-testid="followup-job-select"
                >
                  <option value="">Select an approved job requirement...</option>
                  {approvedJobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.company_name} — {j.title}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Reported Candidate Status (Authoritative metric) *
                </label>
                <input
                  type="text"
                  placeholder="e.g. Technical Round Evaluation ongoing..."
                  value={candidateStatusReported}
                  onChange={(e) => setCandidateStatusReported(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  required
                  data-testid="followup-candidate-status-input"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Pending Rounds (Authoritative metric)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Managerial round pending for 5 students"
                  value={pendingRoundsText}
                  onChange={(e) => setPendingRoundsText(e.target.value)}
                  className="w-full border rounded-md px-3 py-2 text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Expected Result Date (Authoritative metric)
                  </label>
                  <input
                    type="date"
                    value={expectedResultDate}
                    onChange={(e) => setExpectedResultDate(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                    Next Callback Date
                  </label>
                  <input
                    type="date"
                    value={nextFollowUpDate}
                    onChange={(e) => setNextFollowUpDate(e.target.value)}
                    className="w-full border rounded-md px-3 py-2 text-sm"
                  />
                </div>
              </div>

              <label className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isDateConfirmed}
                  onChange={(e) => setIsDateConfirmed(e.target.checked)}
                  className="rounded text-blue-600"
                />
                <span>HR confirmed this as a firm result date (uncheck if tentative estimate)</span>
              </label>

              <div>
                <label className="block text-xs font-semibold text-gray-700 uppercase mb-1">
                  Discussion Summary
                </label>
                <textarea
                  value={followUpSummary}
                  onChange={(e) => setFollowUpSummary(e.target.value)}
                  placeholder="Summary of feedback from corporate HR lead..."
                  className="w-full border rounded-md px-3 py-2 text-sm"
                  rows={2}
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t">
                <Button variant="outline" size="sm" onClick={() => setIsFollowUpModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  type="submit"
                  isLoading={isActionLoading}
                  data-testid="submit-followup-btn"
                >
                  Save Follow-up
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
