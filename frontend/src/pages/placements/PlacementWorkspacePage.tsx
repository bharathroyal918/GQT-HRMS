import React, { useState, useEffect, useCallback } from 'react';
import {
  Award,
  FileCheck,
  Building2,
  Users,
  CheckCircle2,
  XCircle,
  Clock,
  Send,
  Upload,
  Download,
  MapPin,
  RefreshCw,
  Search,
  Layers,
  FileText,
  BadgeCheck,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge, StatusVariant } from '../../components/common/StatusBadge';
import { EmptyState } from '../../components/common/EmptyState';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { placementsApi } from '../../api/placementsApi';
import { jobsApi } from '../../api/jobsApi';
import { useAuth } from '../../context/AuthContext';
import {
  CandidatePlacementStatus,
  CandidateOfferLetter,
  FinalResultIntake,
  PlacementKPIs,
  ParticipatingCandidate,
  CandidatePlacementStatusType,
  OfferAcceptanceStatus,
  JoiningStatus,
  IngestCandidateResultItem,
} from '../../types/placements';
import { JobRequirementListItem } from '../../types/jobs';

export const PlacementWorkspacePage: React.FC = () => {
  const { hasAnyRole } = useAuth();
  const isStaff = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR']);

  // Active Tab
  const [activeTab, setActiveTab] = useState<'statuses' | 'offers' | 'joining' | 'intakes'>('statuses');

  // Loading & Error states
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Data
  const [kpis, setKpis] = useState<PlacementKPIs | null>(null);
  const [statuses, setStatuses] = useState<CandidatePlacementStatus[]>([]);
  const [offers, setOffers] = useState<CandidateOfferLetter[]>([]);
  const [intakes, setIntakes] = useState<FinalResultIntake[]>([]);
  const [approvedJobs, setApprovedJobs] = useState<JobRequirementListItem[]>([]);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedJobId, setSelectedJobId] = useState<string>('');

  // Modals
  const [isIntakeModalOpen, setIsIntakeModalOpen] = useState(false);
  const [isStatusModalOpen, setIsStatusModalOpen] = useState(false);
  const [isNotifyModalOpen, setIsNotifyModalOpen] = useState(false);
  const [isOfferModalOpen, setIsOfferModalOpen] = useState(false);
  const [isResponseModalOpen, setIsResponseModalOpen] = useState(false);
  const [isJoiningModalOpen, setIsJoiningModalOpen] = useState(false);

  // Active item for modal actions
  const [activeStatusItem, setActiveStatusItem] = useState<CandidatePlacementStatus | null>(null);
  const [activeOfferItem, setActiveOfferItem] = useState<CandidateOfferLetter | null>(null);

  // Modal form states: Ingest Results (Step 36)
  const [intakeJobId, setIntakeJobId] = useState('');
  const [participatingCandidates, setParticipatingCandidates] = useState<ParticipatingCandidate[]>([]);
  const [candidateEntries, setCandidateEntries] = useState<Record<string, IngestCandidateResultItem>>({});
  const [intakeSource, setIntakeSource] = useState<'EMAIL' | 'PORTAL' | 'SPREADSHEET_IMPORT' | 'DIRECT_HANDOFF'>('EMAIL');
  const [intakeNotes, setIntakeNotes] = useState('');

  // Modal form states: Update Status (Step 37)
  const [newStatusValue, setNewStatusValue] = useState<CandidatePlacementStatusType>('SELECTED');
  const [statusRevisionReason, setStatusRevisionReason] = useState('');
  const [statusCtc, setStatusCtc] = useState('');
  const [statusDesignation, setStatusDesignation] = useState('');
  const [statusLocation, setStatusLocation] = useState('');

  // Modal form states: Student Notification (Step 38)
  const [notifyChannel, setNotifyChannel] = useState<'EMAIL' | 'SMS' | 'WHATSAPP' | 'PORTAL'>('EMAIL');

  // Modal form states: Upload Offer Letter (Step 39)
  const [offerFile, setOfferFile] = useState<File | null>(null);
  const [offerDeadline, setOfferDeadline] = useState('');
  const [offerExpectedJoining, setOfferExpectedJoining] = useState('');
  const [offerLocation, setOfferLocation] = useState('');
  const [offerFileError, setOfferFileError] = useState<string | null>(null);

  // Modal form states: Response Tracking (Step 40)
  const [responseDecision, setResponseDecision] = useState<'ACCEPTED' | 'DECLINED'>('ACCEPTED');
  const [responseNotes, setResponseNotes] = useState('');

  // Modal form states: Joining Verification (Step 41)
  const [joiningStatusChoice, setJoiningStatusChoice] = useState<'JOINED' | 'NOT_JOINED' | 'DEFERRED'>('JOINED');
  const [actualJoiningDate, setActualJoiningDate] = useState('');
  const [deferredJoiningDate, setDeferredJoiningDate] = useState('');
  const [joiningLocationInput, setJoiningLocationInput] = useState('');
  const [employeeIdInput, setEmployeeIdInput] = useState('');
  const [joiningNotesInput, setJoiningNotesInput] = useState('');

  // Fetch initial data
  const fetchData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isStaff) {
        const [kpiRes, statusRes, offerRes, intakeRes, jobsRes] = await Promise.all([
          placementsApi.getKPIs().catch(() => null),
          placementsApi.listStatuses({
            job_id: selectedJobId || undefined,
            status: statusFilter !== 'ALL' ? statusFilter : undefined,
            search: searchQuery || undefined,
          }),
          placementsApi.listOffers({
            job_id: selectedJobId || undefined,
            search: searchQuery || undefined,
          }),
          placementsApi.listIntakes({
            job_id: selectedJobId || undefined,
            search: searchQuery || undefined,
          }),
          jobsApi.getJobs({ status: 'APPROVED' }).then((r) => r.data).catch(() => []),
        ]);

        setKpis(kpiRes);
        setStatuses(statusRes);
        setOffers(offerRes);
        setIntakes(intakeRes);
        setApprovedJobs(jobsRes);
      } else {
        // Student Portal View
        const myPlacements = await placementsApi.getMyPlacements();
        setStatuses(myPlacements);
        const myOffers = myPlacements
          .filter((p) => p.offer_letter)
          .map((p) => p.offer_letter as CandidateOfferLetter);
        setOffers(myOffers);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load placement workspace data.');
    } finally {
      setIsLoading(false);
    }
  }, [isStaff, selectedJobId, statusFilter, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Load participating candidates when selecting a job in Ingest modal
  const handleIntakeJobChange = async (jobId: string) => {
    setIntakeJobId(jobId);
    setParticipatingCandidates([]);
    setCandidateEntries({});
    if (!jobId) return;

    try {
      const candidates = await placementsApi.getParticipatingCandidates(jobId);
      setParticipatingCandidates(candidates);
      const initialMap: Record<string, IngestCandidateResultItem> = {};
      candidates.forEach((c) => {
        initialMap[c.student_id] = {
          student_id: c.student_id,
          status: 'SELECTED',
          designation_offered: '',
          offered_ctc: null,
          work_location: '',
        };
      });
      setCandidateEntries(initialMap);
    } catch (err: any) {
      setError('Failed to fetch eligible participating candidates for this drive.');
    }
  };

  // Submit Ingest Final Results (Step 36)
  const handleSubmitIntake = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!intakeJobId) return;

    const selectedJob = approvedJobs.find((j) => j.id === intakeJobId);
    if (!selectedJob) return;

    const activeList = Object.values(candidateEntries).filter((entry) => entry.student_id);
    if (activeList.length === 0) {
      alert('Please select at least one candidate for final result ingestion.');
      return;
    }

    setIsSubmitting(true);
    try {
      await placementsApi.createIntake({
        job_requirement_id: intakeJobId,
        company_id: selectedJob.company,
        hr_contact_id: selectedJob.hr_contact || null,
        source: intakeSource,
        notes: intakeNotes,
        candidate_results: activeList,
      });
      setActionSuccess('Final results intake successfully recorded and candidates updated.');
      setIsIntakeModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record final results.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Update Status (Step 37)
  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeStatusItem) return;

    if (activeStatusItem.status === 'SELECTED' && newStatusValue !== 'SELECTED' && !statusRevisionReason.trim()) {
      alert('A documented justification reason is mandatory when revoking candidate selection.');
      return;
    }

    setIsSubmitting(true);
    try {
      await placementsApi.updateStatus(activeStatusItem.id, {
        status: newStatusValue,
        reason: statusRevisionReason,
        offered_ctc: statusCtc ? parseFloat(statusCtc) : null,
        designation_offered: statusDesignation,
        work_location: statusLocation,
      });
      setActionSuccess(`Candidate ${activeStatusItem.student_name} status updated to ${newStatusValue}.`);
      setIsStatusModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update candidate status.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Notification (Step 38)
  const handleSendNotification = async () => {
    if (!activeStatusItem) return;

    setIsSubmitting(true);
    try {
      const res = await placementsApi.notifyCandidate(activeStatusItem.id, notifyChannel);
      setActionSuccess(`Placement advisory dispatched via ${notifyChannel} to ${res.recipient_email}.`);
      setIsNotifyModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to dispatch student notification.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Offer Letter File Selection (Step 39)
  const handleOfferFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setOfferFileError(null);
    if (!file) {
      setOfferFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setOfferFileError('Only valid PDF documents (.pdf) are permitted.');
      setOfferFile(null);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setOfferFileError('File size exceeds the 5MB maximum limit.');
      setOfferFile(null);
      return;
    }

    setOfferFile(file);
  };

  // Submit Upload Offer Letter (Step 39)
  const handleUploadOffer = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeStatusItem || !offerFile) return;

    const formData = new FormData();
    formData.append('placement_id', activeStatusItem.id);
    formData.append('file', offerFile);
    if (offerDeadline) formData.append('acceptance_deadline', offerDeadline);
    if (offerExpectedJoining) formData.append('expected_joining_date', offerExpectedJoining);
    if (offerLocation) formData.append('joining_location', offerLocation);

    setIsSubmitting(true);
    try {
      await placementsApi.uploadOffer(formData);
      setActionSuccess(`Official offer letter uploaded successfully for ${activeStatusItem.student_name}.`);
      setIsOfferModalOpen(false);
      setOfferFile(null);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to upload offer letter.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Offer Response (Step 40)
  const handleOfferResponse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOfferItem) return;

    setIsSubmitting(true);
    try {
      await placementsApi.respondToOffer(activeOfferItem.id, {
        decision: responseDecision,
        notes: responseNotes,
        source: isStaff ? 'PLACEMENT_OFFICE' : 'STUDENT_PORTAL',
      });
      setActionSuccess(`Offer decision [${responseDecision}] recorded successfully.`);
      setIsResponseModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to record offer decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Joining Verification (Step 41)
  const handleVerifyJoining = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeOfferItem) return;

    if (joiningStatusChoice === 'DEFERRED' && !deferredJoiningDate && !joiningNotesInput.trim()) {
      alert('A deferred joining date or explanatory reason is required when deferring joining.');
      return;
    }

    setIsSubmitting(true);
    try {
      await placementsApi.verifyJoining(activeOfferItem.id, {
        joining_status: joiningStatusChoice,
        actual_joining_date: actualJoiningDate || null,
        deferred_joining_date: deferredJoiningDate || null,
        joining_location: joiningLocationInput,
        employee_id_assigned: employeeIdInput,
        notes: joiningNotesInput,
      });
      setActionSuccess(`Candidate joining status verified as [${joiningStatusChoice}].`);
      setIsJoiningModalOpen(false);
      fetchData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to update joining verification.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper status badge variant
  const getStatusBadgeVariant = (st: CandidatePlacementStatusType): StatusVariant => {
    switch (st) {
      case 'SELECTED':
        return 'success';
      case 'REJECTED':
        return 'danger';
      case 'WAITING_LIST':
        return 'warning';
      case 'HOLD':
        return 'info';
      default:
        return 'neutral';
    }
  };

  const getAcceptanceBadgeVariant = (st: OfferAcceptanceStatus): StatusVariant => {
    switch (st) {
      case 'ACCEPTED':
        return 'success';
      case 'DECLINED':
        return 'danger';
      case 'PENDING_RESPONSE':
        return 'warning';
      case 'EXPIRED':
        return 'neutral';
      default:
        return 'neutral';
    }
  };

  const getJoiningBadgeVariant = (st: JoiningStatus): StatusVariant => {
    switch (st) {
      case 'JOINED':
        return 'success';
      case 'NOT_JOINED':
        return 'danger';
      case 'DEFERRED':
        return 'warning';
      case 'PENDING_JOINING':
        return 'info';
      default:
        return 'neutral';
    }
  };

  if (isLoading && !statuses.length) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <LoadingState message="Loading placement management workspace..." />
      </div>
    );
  }

  if (error && !statuses.length) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <ErrorState message={error} onRetry={fetchData} />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-gqt-blue">
            <Award className="w-4 h-4 text-gqt-blue" />
            Phase 8: Placement Management & Tracking (Workflow Steps 36–41)
          </div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-gqt-navy mt-1 tracking-tight">
            Placement Management
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Authoritative corporate result intake, candidate status transitions, student notifications, secure offer letters, and joining verification.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchData} disabled={isLoading} className="gap-1.5">
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {isStaff && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                setIntakeJobId('');
                setParticipatingCandidates([]);
                setIsIntakeModalOpen(true);
              }}
              className="gap-1.5"
            >
              <Upload className="w-4 h-4" />
              Ingest Final Results
            </Button>
          )}
        </div>
      </div>

      {/* Success banner */}
      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-center justify-between text-emerald-800 text-sm">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
            <span>{actionSuccess}</span>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-600 hover:text-emerald-900 font-semibold text-xs">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Cards (Staff View) */}
      {isStaff && kpis && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <Card className="p-4 border-l-4 border-l-gqt-blue">
            <div className="text-xs font-medium text-gqt-neutral-500">Total Results</div>
            <div className="text-2xl font-bold text-gqt-navy mt-1">{kpis.total_results}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Ingested via HR</div>
          </Card>

          <Card className="p-4 border-l-4 border-l-emerald-500">
            <div className="text-xs font-medium text-emerald-700">Selected</div>
            <div className="text-2xl font-bold text-emerald-700 mt-1">{kpis.selected_count}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Eligible for Offers</div>
          </Card>

          <Card className="p-4 border-l-4 border-l-amber-500">
            <div className="text-xs font-medium text-amber-700">Offers Issued</div>
            <div className="text-2xl font-bold text-amber-700 mt-1">{kpis.total_offers}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Pending: {kpis.offers_pending}</div>
          </Card>

          <Card className="p-4 border-l-4 border-l-emerald-600">
            <div className="text-xs font-medium text-emerald-800">Accepted</div>
            <div className="text-2xl font-bold text-emerald-800 mt-1">{kpis.offers_accepted}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Declined: {kpis.offers_declined}</div>
          </Card>

          <Card className="p-4 border-l-4 border-l-indigo-600">
            <div className="text-xs font-medium text-indigo-700">Joined</div>
            <div className="text-2xl font-bold text-indigo-700 mt-1">{kpis.total_joined}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Verified Onboarded</div>
          </Card>

          <Card className="p-4 border-l-4 border-l-purple-500">
            <div className="text-xs font-medium text-purple-700">Deferred</div>
            <div className="text-2xl font-bold text-purple-700 mt-1">{kpis.total_deferred}</div>
            <div className="text-[11px] text-gqt-neutral-500 mt-1">Revised Date Logged</div>
          </Card>
        </div>
      )}

      {/* Workspace Tabs & Filter Toolbar */}
      {isStaff ? (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-gqt-neutral-200">
            <div className="flex gap-1 overflow-x-auto">
              <button
                onClick={() => setActiveTab('statuses')}
                className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'statuses'
                    ? 'border-gqt-blue text-gqt-blue'
                    : 'border-transparent text-gqt-neutral-600 hover:text-gqt-navy'
                  }`}
              >
                <Users className="w-4 h-4" />
                Candidate Statuses (Step 37)
              </button>

              <button
                onClick={() => setActiveTab('offers')}
                className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'offers'
                    ? 'border-gqt-blue text-gqt-blue'
                    : 'border-transparent text-gqt-neutral-600 hover:text-gqt-navy'
                  }`}
              >
                <FileCheck className="w-4 h-4" />
                Offer Letters & Acceptance (Steps 39–40)
              </button>

              <button
                onClick={() => setActiveTab('joining')}
                className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'joining'
                    ? 'border-gqt-blue text-gqt-blue'
                    : 'border-transparent text-gqt-neutral-600 hover:text-gqt-navy'
                  }`}
              >
                <BadgeCheck className="w-4 h-4" />
                Joining Verification (Step 41)
              </button>

              <button
                onClick={() => setActiveTab('intakes')}
                className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors flex items-center gap-2 whitespace-nowrap ${activeTab === 'intakes'
                    ? 'border-gqt-blue text-gqt-blue'
                    : 'border-transparent text-gqt-neutral-600 hover:text-gqt-navy'
                  }`}
              >
                <Layers className="w-4 h-4" />
                Intake Batches (Step 36)
              </button>
            </div>
          </div>

          {/* Search & Filters */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[240px]">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gqt-neutral-400" />
              <input
                type="text"
                placeholder="Search by student name, roll number, or company..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue focus:border-transparent"
              />
            </div>

            {activeTab === 'statuses' && (
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-3 py-1.5 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="ALL">All Statuses</option>
                <option value="SELECTED">Selected</option>
                <option value="REJECTED">Rejected</option>
                <option value="WAITING_LIST">Waiting List</option>
                <option value="HOLD">Hold</option>
              </select>
            )}

            {approvedJobs.length > 0 && (
              <select
                value={selectedJobId}
                onChange={(e) => setSelectedJobId(e.target.value)}
                className="px-3 py-1.5 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue max-w-xs"
              >
                <option value="">All Recruitment Drives</option>
                {approvedJobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} ({j.company_name})
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>
      ) : (
        /* Student Portal Header */
        <div className="bg-gqt-blue-light/30 border border-blue-200/80 p-4 rounded-xl flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-gqt-navy">My Placement Opportunities & Offers</h2>
            <p className="text-xs text-gqt-neutral-600 mt-0.5">
              Review your drive selection results, download authorized offer letters, and submit your acceptance response.
            </p>
          </div>
          <span className="px-3 py-1 bg-white border border-blue-200 text-xs font-semibold text-gqt-blue rounded-full shadow-sm">
            Candidate Self-Service
          </span>
        </div>
      )}

      {/* TAB 1: Candidate Statuses & Notifications (Step 37 & 38) */}
      {(activeTab === 'statuses' || !isStaff) && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-gqt-neutral-200 bg-gqt-neutral-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gqt-navy">
              {isStaff ? 'Candidate Results & Placement Decisions (Step 37)' : 'My Placement Decisions'}
            </h3>
            <span className="text-xs text-gqt-neutral-500 font-medium">
              Showing {statuses.length} record{statuses.length === 1 ? '' : 's'}
            </span>
          </div>

          {statuses.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No placement records found"
                description={
                  isStaff
                    ? 'No candidate placement records match the current criteria. Ingest final results from corporate HR to get started.'
                    : 'You do not have any placement outcomes recorded for your profile yet.'
                }
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gqt-neutral-100/70 text-gqt-neutral-600 font-semibold text-xs border-b border-gqt-neutral-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Drive & Company</th>
                    <th className="py-3 px-4">Placement Status</th>
                    <th className="py-3 px-4">Terms Offered</th>
                    <th className="py-3 px-4">Offer Letter</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-200">
                  {statuses.map((item) => (
                    <tr key={item.id} className="hover:bg-gqt-neutral-50/80 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gqt-navy">{item.student_name}</div>
                        <div className="text-xs text-gqt-neutral-500 font-mono">{item.student_roll}</div>
                        <div className="text-xs text-gqt-neutral-400">{item.student_email}</div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-gqt-navy">{item.job_title}</div>
                        <div className="text-xs text-gqt-neutral-500 flex items-center gap-1 mt-0.5">
                          <Building2 className="w-3.5 h-3.5 text-gqt-neutral-400" />
                          {item.company_name}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={getStatusBadgeVariant(item.status)}
                          label={item.status_display || item.status}
                        />
                        {item.status_updated_at && (
                          <div className="text-[11px] text-gqt-neutral-400 mt-1">
                            {new Date(item.status_updated_at).toLocaleDateString()}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {item.offered_ctc ? (
                          <div className="font-semibold text-emerald-700">₹{Number(item.offered_ctc).toLocaleString()} LPA</div>
                        ) : (
                          <span className="text-gqt-neutral-400">Standard Drive CTC</span>
                        )}
                        {item.designation_offered && (
                          <div className="text-gqt-neutral-600 mt-0.5">{item.designation_offered}</div>
                        )}
                        {item.work_location && (
                          <div className="text-gqt-neutral-400 flex items-center gap-0.5 mt-0.5">
                            <MapPin className="w-3 h-3" />
                            {item.work_location}
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-4">
                        {item.has_offer_letter && item.offer_letter_id ? (
                          <div className="space-y-1">
                            <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              <FileCheck className="w-3.5 h-3.5" />
                              Uploaded
                            </span>
                            <div className="text-xs">
                              <a
                                href={placementsApi.getOfferDownloadUrl(item.offer_letter_id)}
                                target="_blank"
                                rel="noreferrer"
                                className="text-gqt-blue hover:underline inline-flex items-center gap-1 font-medium"
                              >
                                <Download className="w-3 h-3" />
                                Download PDF
                              </a>
                            </div>
                          </div>
                        ) : item.status === 'SELECTED' ? (
                          <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                            Awaiting Upload
                          </span>
                        ) : (
                          <span className="text-xs text-gqt-neutral-400">N/A</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {isStaff && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setActiveStatusItem(item);
                                  setNewStatusValue(item.status);
                                  setStatusRevisionReason('');
                                  setStatusCtc(item.offered_ctc ? String(item.offered_ctc) : '');
                                  setStatusDesignation(item.designation_offered || '');
                                  setStatusLocation(item.work_location || '');
                                  setIsStatusModalOpen(true);
                                }}
                                title="Update Status (Step 37)"
                              >
                                Update Status
                              </Button>

                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setActiveStatusItem(item);
                                  setIsNotifyModalOpen(true);
                                }}
                                title="Notify Student (Step 38)"
                                className="text-gqt-blue border-blue-200 hover:bg-blue-50"
                              >
                                <Send className="w-3.5 h-3.5" />
                              </Button>

                              {item.status === 'SELECTED' && (
                                <Button
                                  variant="primary"
                                  size="sm"
                                  onClick={() => {
                                    setActiveStatusItem(item);
                                    setOfferFile(null);
                                    setOfferFileError(null);
                                    setOfferDeadline('');
                                    setOfferExpectedJoining('');
                                    setOfferLocation(item.work_location || '');
                                    setIsOfferModalOpen(true);
                                  }}
                                  title="Upload Official Offer Letter (Step 39)"
                                >
                                  <Upload className="w-3.5 h-3.5 mr-1" />
                                  Offer
                                </Button>
                              )}
                            </>
                          )}

                          {/* Student Response Action */}
                          {!isStaff && item.has_offer_letter && item.offer_letter && (
                            <Button
                              variant="primary"
                              size="sm"
                              onClick={() => {
                                setActiveOfferItem(item.offer_letter!);
                                setIsResponseModalOpen(true);
                              }}
                              disabled={item.offer_letter.acceptance_status !== 'PENDING_RESPONSE'}
                            >
                              {item.offer_letter.acceptance_status === 'PENDING_RESPONSE'
                                ? 'Respond to Offer'
                                : item.offer_letter.acceptance_status_display}
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* TAB 2: Offer Letters & Acceptance (Step 39 & 40) */}
      {isStaff && activeTab === 'offers' && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-gqt-neutral-200 bg-gqt-neutral-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gqt-navy">Offer Letters & Response Lifecycle (Steps 39 & 40)</h3>
            <span className="text-xs text-gqt-neutral-500 font-medium">
              Showing {offers.length} offer{offers.length === 1 ? '' : 's'}
            </span>
          </div>

          {offers.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No offer letters issued yet"
                description="Upload official offer letters for candidates in SELECTED status to initiate acceptance tracking."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gqt-neutral-100/70 text-gqt-neutral-600 font-semibold text-xs border-b border-gqt-neutral-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Document Details</th>
                    <th className="py-3 px-4">Acceptance Status</th>
                    <th className="py-3 px-4">Response Deadline</th>
                    <th className="py-3 px-4">Candidate Decision</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-200">
                  {offers.map((offer) => (
                    <tr key={offer.id} className="hover:bg-gqt-neutral-50/80 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gqt-navy">{offer.file_name}</div>
                        <div className="text-xs text-gqt-neutral-500">v{offer.version_number} &bull; {(offer.file_size_bytes / 1024).toFixed(1)} KB</div>
                        <div className="text-[11px] font-mono text-gqt-neutral-400 truncate max-w-[180px]">
                          SHA: {offer.sha256_hash.substring(0, 16)}...
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <a
                          href={placementsApi.getOfferDownloadUrl(offer.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-xs font-semibold text-gqt-blue bg-blue-50 px-2.5 py-1 rounded border border-blue-200 hover:bg-blue-100 transition-colors"
                        >
                          <Download className="w-3.5 h-3.5" />
                          Download PDF
                        </a>
                        <div className="text-[11px] text-gqt-neutral-400 mt-1">
                          Uploaded: {new Date(offer.issued_at).toLocaleDateString()}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={getAcceptanceBadgeVariant(offer.acceptance_status)}
                          label={offer.acceptance_status_display}
                        />
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {offer.acceptance_deadline ? (
                          <div className="flex items-center gap-1 text-gqt-neutral-700">
                            <Clock className="w-3.5 h-3.5 text-gqt-neutral-400" />
                            {new Date(offer.acceptance_deadline).toLocaleDateString()}
                          </div>
                        ) : (
                          <span className="text-gqt-neutral-400 italic">No hard deadline</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {offer.accepted_at ? (
                          <div>
                            <div className="font-medium text-gqt-navy">
                              {offer.acceptance_source === 'STUDENT_PORTAL' ? 'Self-Service Portal' : 'Offline Staff Entry'}
                            </div>
                            <div className="text-gqt-neutral-400">{new Date(offer.accepted_at).toLocaleDateString()}</div>
                            {offer.student_decision_notes && (
                              <div className="text-gqt-neutral-600 mt-0.5 truncate max-w-[200px]" title={offer.student_decision_notes}>
                                "{offer.student_decision_notes}"
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-gqt-neutral-400">Awaiting Response</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          {offer.acceptance_status === 'PENDING_RESPONSE' && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => {
                                setActiveOfferItem(offer);
                                setResponseDecision('ACCEPTED');
                                setResponseNotes('');
                                setIsResponseModalOpen(true);
                              }}
                            >
                              Record Response
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* TAB 3: Joining Verification (Step 41) */}
      {isStaff && activeTab === 'joining' && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-gqt-neutral-200 bg-gqt-neutral-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gqt-navy">Joining Status & Candidate Reporting (Step 41)</h3>
            <span className="text-xs text-gqt-neutral-500 font-medium">
              Tracking accepted candidates
            </span>
          </div>

          {offers.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No accepted offers available"
                description="Once candidates accept their offer letters, track their formal onboarding and reporting status here."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gqt-neutral-100/70 text-gqt-neutral-600 font-semibold text-xs border-b border-gqt-neutral-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Offer / Document</th>
                    <th className="py-3 px-4">Joining Status</th>
                    <th className="py-3 px-4">Expected Date</th>
                    <th className="py-3 px-4">Actual / Deferred Date</th>
                    <th className="py-3 px-4">Employee ID</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-200">
                  {offers.map((offer) => (
                    <tr key={offer.id} className="hover:bg-gqt-neutral-50/80 transition-colors">
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gqt-navy">{offer.file_name}</div>
                        <div className="text-xs text-gqt-neutral-500">
                          Accepted: {offer.acceptance_status === 'ACCEPTED' ? 'Yes' : 'Pending'}
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={getJoiningBadgeVariant(offer.joining_status)}
                          label={offer.joining_status_display}
                        />
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {offer.expected_joining_date ? (
                          new Date(offer.expected_joining_date).toLocaleDateString()
                        ) : (
                          <span className="text-gqt-neutral-400 italic">Not set</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {offer.joining_status === 'JOINED' && offer.actual_joining_date ? (
                          <span className="text-emerald-700 font-semibold">
                            Joined: {new Date(offer.actual_joining_date).toLocaleDateString()}
                          </span>
                        ) : offer.joining_status === 'DEFERRED' && offer.deferred_joining_date ? (
                          <span className="text-amber-700 font-semibold">
                            Deferred to: {new Date(offer.deferred_joining_date).toLocaleDateString()}
                          </span>
                        ) : (
                          <span className="text-gqt-neutral-400">Pending Date</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-xs">
                        {offer.employee_id_assigned ? (
                          <span className="font-mono bg-gqt-neutral-100 px-2 py-0.5 rounded text-gqt-navy font-semibold">
                            {offer.employee_id_assigned}
                          </span>
                        ) : (
                          <span className="text-gqt-neutral-400 italic">Unassigned</span>
                        )}
                      </td>

                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setActiveOfferItem(offer);
                            setJoiningStatusChoice(offer.joining_status === 'NOT_APPLICABLE' ? 'JOINED' : (offer.joining_status as any));
                            setActualJoiningDate(offer.actual_joining_date || '');
                            setDeferredJoiningDate(offer.deferred_joining_date || '');
                            setJoiningLocationInput(offer.joining_location || '');
                            setEmployeeIdInput(offer.employee_id_assigned || '');
                            setJoiningNotesInput(offer.joining_notes || '');
                            setIsJoiningModalOpen(true);
                          }}
                        >
                          Verify Status
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* TAB 4: Intake Batches (Step 36) */}
      {isStaff && activeTab === 'intakes' && (
        <Card className="overflow-hidden">
          <div className="p-4 border-b border-gqt-neutral-200 bg-gqt-neutral-50 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gqt-navy">Final Result Ingestion Batches (Step 36)</h3>
            <span className="text-xs text-gqt-neutral-500 font-medium">
              Showing {intakes.length} intake{intakes.length === 1 ? '' : 's'}
            </span>
          </div>

          {intakes.length === 0 ? (
            <div className="p-8">
              <EmptyState
                title="No intake batches recorded"
                description="Click 'Ingest Final Results' to record corporate recruitment outcomes."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-gqt-neutral-100/70 text-gqt-neutral-600 font-semibold text-xs border-b border-gqt-neutral-200 uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Reference Code</th>
                    <th className="py-3 px-4">Drive & Company</th>
                    <th className="py-3 px-4">Source</th>
                    <th className="py-3 px-4">Breakdown</th>
                    <th className="py-3 px-4">Received / Recorded By</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-200">
                  {intakes.map((batch) => (
                    <tr key={batch.id} className="hover:bg-gqt-neutral-50/80 transition-colors">
                      <td className="py-3 px-4">
                        <span className="font-mono font-bold text-gqt-blue text-xs bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                          {batch.result_reference_code}
                        </span>
                      </td>

                      <td className="py-3 px-4">
                        <div className="font-medium text-gqt-navy">{batch.job_title}</div>
                        <div className="text-xs text-gqt-neutral-500">{batch.company_name}</div>
                      </td>

                      <td className="py-3 px-4 text-xs text-gqt-neutral-700">
                        {batch.source_display}
                      </td>

                      <td className="py-3 px-4 text-xs">
                        <div className="flex gap-2">
                          <span className="text-emerald-700 font-medium">{batch.selected_count} Selected</span>
                          <span className="text-rose-700 font-medium">{batch.rejected_count} Rejected</span>
                          <span className="text-amber-700 font-medium">{batch.waiting_list_count} Waiting</span>
                          <span className="text-indigo-700 font-medium">{batch.hold_count} Hold</span>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-xs text-gqt-neutral-500">
                        <div>{new Date(batch.received_at).toLocaleDateString()}</div>
                        <div className="text-gqt-neutral-400">By {batch.created_by_name}</div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 1: Ingest Final Results (Step 36) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isIntakeModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleSubmitIntake} className="p-6 space-y-5">
              <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
                <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                  <Upload className="w-5 h-5 text-gqt-blue" />
                  Ingest Final Results from Corporate HR (Step 36)
                </h3>
                <button
                  type="button"
                  onClick={() => setIsIntakeModalOpen(false)}
                  className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
                >
                  &times;
                </button>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                  Approved Recruitment Drive *
                </label>
                <select
                  required
                  value={intakeJobId}
                  onChange={(e) => handleIntakeJobChange(e.target.value)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="">Select recruitment drive...</option>
                  {approvedJobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} &mdash; {j.company_name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Intake Source</label>
                  <select
                    value={intakeSource}
                    onChange={(e) => setIntakeSource(e.target.value as any)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  >
                    <option value="EMAIL">Corporate HR Email</option>
                    <option value="PORTAL">Corporate Recruiter Portal</option>
                    <option value="SPREADSHEET_IMPORT">Spreadsheet Roster Export</option>
                    <option value="DIRECT_HANDOFF">Direct Campus Drive Handoff</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Batch Notes</label>
                  <input
                    type="text"
                    value={intakeNotes}
                    onChange={(e) => setIntakeNotes(e.target.value)}
                    placeholder="e.g. Official final selection roster"
                    className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  />
                </div>
              </div>

              {/* Participating candidates list */}
              {intakeJobId && (
                <div className="border border-gqt-neutral-200 rounded-lg p-3 space-y-3">
                  <div className="flex items-center justify-between text-xs font-semibold text-gqt-navy">
                    <span>Participating Candidates in this Drive ({participatingCandidates.length})</span>
                    <span className="text-gqt-neutral-500 font-normal">Assign outcome decisions</span>
                  </div>

                  {participatingCandidates.length === 0 ? (
                    <div className="p-4 text-center text-xs text-gqt-neutral-500">
                      No candidates were found submitted or shortlisted for this drive.
                    </div>
                  ) : (
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                      {participatingCandidates.map((c) => {
                        const entry = candidateEntries[c.student_id] || {
                          student_id: c.student_id,
                          status: 'SELECTED',
                          designation_offered: '',
                          offered_ctc: null,
                          work_location: '',
                        };

                        return (
                          <div
                            key={c.student_id}
                            className="p-2.5 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-200 space-y-2"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <span className="font-semibold text-xs text-gqt-navy">{c.student_name}</span>
                                <span className="text-[11px] font-mono text-gqt-neutral-500 ml-2">({c.roll_number})</span>
                              </div>

                              <select
                                value={entry.status}
                                onChange={(e) => {
                                  const updated = { ...candidateEntries };
                                  updated[c.student_id] = {
                                    ...entry,
                                    status: e.target.value as CandidatePlacementStatusType,
                                  };
                                  setCandidateEntries(updated);
                                }}
                                className="text-xs px-2 py-1 font-semibold rounded border border-gqt-neutral-300 bg-white"
                              >
                                <option value="SELECTED">SELECTED</option>
                                <option value="REJECTED">REJECTED</option>
                                <option value="WAITING_LIST">WAITING_LIST</option>
                                <option value="HOLD">HOLD</option>
                              </select>
                            </div>

                            {entry.status === 'SELECTED' && (
                              <div className="grid grid-cols-3 gap-2 text-xs">
                                <input
                                  type="text"
                                  placeholder="Designation"
                                  value={entry.designation_offered || ''}
                                  onChange={(e) => {
                                    const updated = { ...candidateEntries };
                                    updated[c.student_id] = { ...entry, designation_offered: e.target.value };
                                    setCandidateEntries(updated);
                                  }}
                                  className="px-2 py-1 border border-gqt-neutral-300 rounded"
                                />
                                <input
                                  type="number"
                                  placeholder="Offered CTC (₹)"
                                  value={entry.offered_ctc || ''}
                                  onChange={(e) => {
                                    const updated = { ...candidateEntries };
                                    updated[c.student_id] = {
                                      ...entry,
                                      offered_ctc: e.target.value ? parseFloat(e.target.value) : null,
                                    };
                                    setCandidateEntries(updated);
                                  }}
                                  className="px-2 py-1 border border-gqt-neutral-300 rounded"
                                />
                                <input
                                  type="text"
                                  placeholder="Location"
                                  value={entry.work_location || ''}
                                  onChange={(e) => {
                                    const updated = { ...candidateEntries };
                                    updated[c.student_id] = { ...entry, work_location: e.target.value };
                                    setCandidateEntries(updated);
                                  }}
                                  className="px-2 py-1 border border-gqt-neutral-300 rounded"
                                />
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
                <Button type="button" variant="outline" onClick={() => setIsIntakeModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={isSubmitting || participatingCandidates.length === 0}
                >
                  {isSubmitting ? 'Recording Batch...' : 'Confirm Final Results'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 2: Update Candidate Status (Step 37) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isStatusModalOpen && activeStatusItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full">
            <form onSubmit={handleUpdateStatus} className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
                <h3 className="text-lg font-bold text-gqt-navy">Update Candidate Status (Step 37)</h3>
                <button
                  type="button"
                  onClick={() => setIsStatusModalOpen(false)}
                  className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
                >
                  &times;
                </button>
              </div>

              <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200">
                Candidate: <strong className="text-gqt-navy">{activeStatusItem.student_name}</strong> ({activeStatusItem.student_roll})<br />
                Drive: <strong>{activeStatusItem.job_title}</strong> &bull; {activeStatusItem.company_name}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">New Status *</label>
                <select
                  value={newStatusValue}
                  onChange={(e) => setNewStatusValue(e.target.value as any)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="SELECTED">SELECTED</option>
                  <option value="REJECTED">REJECTED</option>
                  <option value="WAITING_LIST">WAITING_LIST</option>
                  <option value="HOLD">HOLD</option>
                </select>
              </div>

              {activeStatusItem.status === 'SELECTED' && newStatusValue !== 'SELECTED' && (
                <div>
                  <label className="block text-xs font-semibold text-rose-700 uppercase mb-1">
                    Revocation Justification Reason *
                  </label>
                  <textarea
                    required
                    rows={2}
                    placeholder="Documented justification is mandatory when revoking candidate selection..."
                    value={statusRevisionReason}
                    onChange={(e) => setStatusRevisionReason(e.target.value)}
                    className="w-full px-3 py-2 text-sm rounded-lg border border-rose-300 focus:outline-none focus:ring-2 focus:ring-rose-500"
                  />
                </div>
              )}

              {newStatusValue === 'SELECTED' && (
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Offered CTC (₹)</label>
                    <input
                      type="number"
                      value={statusCtc}
                      onChange={(e) => setStatusCtc(e.target.value)}
                      placeholder="e.g. 850000"
                      className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Designation</label>
                    <input
                      type="text"
                      value={statusDesignation}
                      onChange={(e) => setStatusDesignation(e.target.value)}
                      placeholder="e.g. Associate Engineer"
                      className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
                <Button type="button" variant="outline" onClick={() => setIsStatusModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Saving...' : 'Update Status'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 3: Notify Student (Step 38) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isNotifyModalOpen && activeStatusItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
              <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                <Send className="w-5 h-5 text-gqt-blue" />
                Notify Candidate (Step 38)
              </h3>
              <button
                type="button"
                onClick={() => setIsNotifyModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200 space-y-1">
              <div><strong>Candidate:</strong> {activeStatusItem.student_name} ({activeStatusItem.student_roll})</div>
              <div><strong>Institutional Email:</strong> {activeStatusItem.student_email}</div>
              <div><strong>Outcome Decision:</strong> <StatusBadge variant={getStatusBadgeVariant(activeStatusItem.status)} label={activeStatusItem.status} /></div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Communication Channel</label>
              <select
                value={notifyChannel}
                onChange={(e) => setNotifyChannel(e.target.value as any)}
                className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="EMAIL">Direct Institutional Email</option>
                <option value="PORTAL">Student Career Portal Notification</option>
                <option value="SMS">SMS Advisory</option>
                <option value="WHATSAPP">WhatsApp Enterprise Message</option>
              </select>
            </div>

            <div className="p-3 bg-blue-50/60 border border-blue-200 rounded-lg text-xs text-gqt-neutral-700">
              <span className="font-semibold text-gqt-blue">Truthful Dispatch Policy:</span> If external SMS or WhatsApp gateways are unconfigured in development, an honest simulated transmission log will be recorded.
            </div>

            <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
              <Button type="button" variant="outline" onClick={() => setIsNotifyModalOpen(false)}>
                Cancel
              </Button>
              <Button type="button" variant="primary" onClick={handleSendNotification} disabled={isSubmitting}>
                {isSubmitting ? 'Dispatching...' : 'Send Notification'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 4: Upload Offer Letter (Step 39) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isOfferModalOpen && activeStatusItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full">
            <form onSubmit={handleUploadOffer} className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
                <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                  <FileText className="w-5 h-5 text-gqt-blue" />
                  Upload Official Offer Letter (Step 39)
                </h3>
                <button
                  type="button"
                  onClick={() => setIsOfferModalOpen(false)}
                  className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
                >
                  &times;
                </button>
              </div>

              <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200">
                Selected Candidate: <strong className="text-gqt-navy">{activeStatusItem.student_name}</strong> &bull; {activeStatusItem.company_name}
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                  Offer Letter PDF Document * (Max 5MB)
                </label>
                <input
                  type="file"
                  required
                  accept=".pdf,application/pdf"
                  onChange={handleOfferFileChange}
                  className="w-full text-xs text-gqt-neutral-600 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-gqt-blue file:text-white hover:file:bg-gqt-blue-dark cursor-pointer border border-gqt-neutral-300 rounded-lg p-1.5"
                />
                {offerFileError && (
                  <p className="text-xs text-rose-600 mt-1 font-semibold">{offerFileError}</p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                    Acceptance Deadline (Optional)
                  </label>
                  <input
                    type="date"
                    value={offerDeadline}
                    onChange={(e) => setOfferDeadline(e.target.value)}
                    className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                    Expected Joining Date
                  </label>
                  <input
                    type="date"
                    value={offerExpectedJoining}
                    onChange={(e) => setOfferExpectedJoining(e.target.value)}
                    className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Joining Location</label>
                <input
                  type="text"
                  placeholder="e.g. Bangalore Campus / Hyderabad Office"
                  value={offerLocation}
                  onChange={(e) => setOfferLocation(e.target.value)}
                  className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                />
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
                <Button type="button" variant="outline" onClick={() => setIsOfferModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={isSubmitting || !offerFile}>
                  {isSubmitting ? 'Uploading...' : 'Upload & Issue Offer'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 5: Offer Response Decision (Step 40) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isResponseModalOpen && activeOfferItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full">
            <form onSubmit={handleOfferResponse} className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
                <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  Record Offer Decision (Step 40)
                </h3>
                <button
                  type="button"
                  onClick={() => setIsResponseModalOpen(false)}
                  className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
                >
                  &times;
                </button>
              </div>

              <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200">
                Offer Letter: <strong className="text-gqt-navy">{activeOfferItem.file_name}</strong> (v{activeOfferItem.version_number})
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Decision *</label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setResponseDecision('ACCEPTED')}
                    className={`py-2 px-3 rounded-lg border text-sm font-semibold flex items-center justify-center gap-1.5 transition-colors ${responseDecision === 'ACCEPTED'
                        ? 'bg-emerald-50 border-emerald-500 text-emerald-700 ring-2 ring-emerald-500/20'
                        : 'border-gqt-neutral-300 text-gqt-neutral-600'
                      }`}
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Accept Offer
                  </button>

                  <button
                    type="button"
                    onClick={() => setResponseDecision('DECLINED')}
                    className={`py-2 px-3 rounded-lg border text-sm font-semibold flex items-center justify-center gap-1.5 transition-colors ${responseDecision === 'DECLINED'
                        ? 'bg-rose-50 border-rose-500 text-rose-700 ring-2 ring-rose-500/20'
                        : 'border-gqt-neutral-300 text-gqt-neutral-600'
                      }`}
                  >
                    <XCircle className="w-4 h-4 text-rose-600" />
                    Decline Offer
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                  {responseDecision === 'DECLINED' ? 'Reason for Declining (Mandatory)' : 'Candidate Decision Remarks'}
                </label>
                <textarea
                  rows={2}
                  value={responseNotes}
                  onChange={(e) => setResponseNotes(e.target.value)}
                  placeholder={
                    responseDecision === 'DECLINED'
                      ? 'Please specify why the offer is declined...'
                      : 'Candidate remarks, joining date acknowledgment...'
                  }
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
                <Button type="button" variant="outline" onClick={() => setIsResponseModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Recording...' : 'Submit Decision'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ----------------------------------------------------------------------------------------- */}
      {/* MODAL 6: Verify Joining Status (Step 41) */}
      {/* ----------------------------------------------------------------------------------------- */}
      {isJoiningModalOpen && activeOfferItem && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full">
            <form onSubmit={handleVerifyJoining} className="p-6 space-y-4">
              <div className="flex items-center justify-between border-b border-gqt-neutral-200 pb-3">
                <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                  <BadgeCheck className="w-5 h-5 text-indigo-600" />
                  Verify Candidate Joining (Step 41)
                </h3>
                <button
                  type="button"
                  onClick={() => setIsJoiningModalOpen(false)}
                  className="text-gqt-neutral-400 hover:text-gqt-navy text-lg font-bold"
                >
                  &times;
                </button>
              </div>

              <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200">
                Offer Letter: <strong className="text-gqt-navy">{activeOfferItem.file_name}</strong>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Joining Outcome *</label>
                <select
                  value={joiningStatusChoice}
                  onChange={(e) => setJoiningStatusChoice(e.target.value as any)}
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="JOINED">JOINED &mdash; Confirmed Onboarding</option>
                  <option value="NOT_JOINED">NOT_JOINED &mdash; Candidate Did Not Report</option>
                  <option value="DEFERRED">DEFERRED &mdash; Joining Date Postponed</option>
                </select>
              </div>

              {joiningStatusChoice === 'JOINED' && (
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Actual Joining Date</label>
                    <input
                      type="date"
                      value={actualJoiningDate}
                      onChange={(e) => setActualJoiningDate(e.target.value)}
                      className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">Employee ID Assigned</label>
                    <input
                      type="text"
                      placeholder="e.g. EMP-9042"
                      value={employeeIdInput}
                      onChange={(e) => setEmployeeIdInput(e.target.value)}
                      className="w-full px-3 py-1.5 border border-gqt-neutral-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

              {joiningStatusChoice === 'DEFERRED' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-semibold text-amber-700 uppercase mb-1">
                      Revised Joining Date (Optional if Reason Provided)
                    </label>
                    <input
                      type="date"
                      value={deferredJoiningDate}
                      onChange={(e) => setDeferredJoiningDate(e.target.value)}
                      className="w-full px-3 py-1.5 border border-amber-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-gqt-navy uppercase mb-1">
                  {joiningStatusChoice === 'DEFERRED' ? 'Deferral Justification (Mandatory if date omitted)' : 'Verification Remarks'}
                </label>
                <textarea
                  rows={2}
                  value={joiningNotesInput}
                  onChange={(e) => setJoiningNotesInput(e.target.value)}
                  placeholder="Onboarding verification details, reporting venue notes..."
                  className="w-full px-3 py-2 text-sm rounded-lg border border-gqt-neutral-300 focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                />
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-gqt-neutral-200 pt-3">
                <Button type="button" variant="outline" onClick={() => setIsJoiningModalOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={isSubmitting}>
                  {isSubmitting ? 'Verifying...' : 'Save Joining Status'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
