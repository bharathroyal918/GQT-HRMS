import React, { useState, useEffect, useCallback } from 'react';
import {
  Send,
  FileSpreadsheet,
  FileCheck,
  CheckCircle2,
  Clock,
  Building2,
  Users,
  CheckCheck,
  AlertCircle,
  Calendar,
  Download,
  RefreshCw,
  Plus,
  Briefcase,
  ShieldCheck,
  FileText,
  Copy,
} from 'lucide-react';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge, StatusVariant } from '../../components/common/StatusBadge';
import { submissionsApi } from '../../api/submissionsApi';
import { jobsApi } from '../../api/jobsApi';
import { useAuth } from '../../context/AuthContext';
import {
  SubmissionPackageListItem,
  SubmissionPackage,
  JobEligibleCandidatesResponse,
} from '../../types/submissions';
import { JobRequirementListItem } from '../../types/jobs';

export const CandidateSubmissionWorkspacePage: React.FC = () => {
  const { user, hasAnyRole } = useAuth();
  const [packages, setPackages] = useState<SubmissionPackageListItem[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<SubmissionPackage | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modals
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isDispatchModalOpen, setIsDispatchModalOpen] = useState(false);
  const [isAcknowledgeModalOpen, setIsAcknowledgeModalOpen] = useState(false);
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Create Package State
  const [approvedJobs, setApprovedJobs] = useState<JobRequirementListItem[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [candidatePool, setCandidatePool] = useState<JobEligibleCandidatesResponse | null>(null);
  const [selectedStudentIds, setSelectedStudentIds] = useState<string[]>([]);
  const [customPackageTitle, setCustomPackageTitle] = useState('');
  const [packageNotes, setPackageNotes] = useState('');
  const [isPoolLoading, setIsPoolLoading] = useState(false);

  // Dispatch Modal State
  const [dispatchChannel, setDispatchChannel] = useState<'EMAIL' | 'WHATSAPP' | 'PORTAL_LINK' | 'DIRECT_HANDOFF'>('EMAIL');
  const [dispatchRecipientEmail, setDispatchRecipientEmail] = useState('');
  const [dispatchRecipientName, setDispatchRecipientName] = useState('');
  const [dispatchRecipientPhone, setDispatchRecipientPhone] = useState('');
  const [dispatchNotes, setDispatchNotes] = useState('');

  // Acknowledgment Modal State
  const [ackContactName, setAckContactName] = useState('');
  const [ackChannel, setAckChannel] = useState<'EMAIL' | 'PHONE_CALL' | 'WHATSAPP' | 'PORTAL' | 'IN_PERSON'>('EMAIL');
  const [ackFeedback, setAckFeedback] = useState('');
  const [ackTentativeDate, setAckTentativeDate] = useState('');
  const [ackCallbackDate, setAckCallbackDate] = useState('');

  const isStaff = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']) || user?.is_staff || false;
  const canAcknowledge = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR']) || user?.is_staff || false;

  // Load packages
  const loadPackages = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await submissionsApi.listPackages(
        statusFilter !== 'ALL' ? { status: statusFilter } : undefined
      );
      setPackages(data);

      const firstPkg = data[0];
      if (firstPkg && !selectedPackage) {
        loadPackageDetails(firstPkg.id);
      } else if (selectedPackage) {
        loadPackageDetails(selectedPackage.id);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load corporate submission packages.');
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  const loadPackageDetails = async (packageId: string) => {
    try {
      const details = await submissionsApi.getPackageById(packageId);
      setSelectedPackage(details);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to load package details.');
    }
  };

  useEffect(() => {
    loadPackages();
  }, [loadPackages]);

  // Load Approved Jobs for creation modal
  const openCreateModal = async () => {
    setIsCreateModalOpen(true);
    setSelectedJobId('');
    setCandidatePool(null);
    setSelectedStudentIds([]);
    setCustomPackageTitle('');
    setPackageNotes('');
    try {
      const jobsRes = await jobsApi.getJobs({ status: 'APPROVED' });
      setApprovedJobs(jobsRes.data || []);
    } catch (err) {
      console.error('Failed to load approved jobs', err);
    }
  };

  // When job is selected, load eligible candidates with Step 23 readiness badges
  const handleJobSelect = async (jobId: string) => {
    setSelectedJobId(jobId);
    setSelectedStudentIds([]);
    if (!jobId) {
      setCandidatePool(null);
      return;
    }
    try {
      setIsPoolLoading(true);
      const pool = await submissionsApi.getEligibleCandidatesForJob(jobId);
      setCandidatePool(pool);
      // Auto-select all candidates who can be submitted
      const readyIds = pool.candidates.filter(c => c.can_be_submitted).map(c => c.student_id);
      setSelectedStudentIds(readyIds);
      setCustomPackageTitle(`${pool.company_name} - ${pool.job_title} Candidate Roster`);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to fetch candidate readiness pool.');
    } finally {
      setIsPoolLoading(false);
    }
  };

  const handleToggleSelectCandidate = (studentId: string) => {
    setSelectedStudentIds(prev =>
      prev.includes(studentId) ? prev.filter(id => id !== studentId) : [...prev, studentId]
    );
  };

  // Step 24: Submit Create Package
  const handleCreatePackage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedJobId || selectedStudentIds.length === 0) return;
    try {
      setIsActionLoading(true);
      setError(null);
      const newPkg = await submissionsApi.createPackage({
        job_requirement_id: selectedJobId,
        candidate_student_ids: selectedStudentIds,
        title: customPackageTitle,
        notes: packageNotes,
      });
      setIsCreateModalOpen(false);
      setActionSuccess(`Submission package '${newPkg.title}' created with ${newPkg.candidate_count} candidates!`);
      setSelectedPackage(newPkg);
      loadPackages();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to assemble submission package.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Step 25: Generate Master Excel Roster
  const handleGenerateRoster = async () => {
    if (!selectedPackage) return;
    try {
      setIsActionLoading(true);
      setError(null);
      const updated = await submissionsApi.generateRoster(selectedPackage.id);
      setSelectedPackage(updated);
      setActionSuccess(`Master candidate roster Excel generated! SHA-256 Digest: ${updated.package_hash.slice(0, 16)}...`);
      loadPackages();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to generate candidate roster spreadsheet.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Step 26: Attach Resumes
  const handleAttachResumes = async () => {
    if (!selectedPackage) return;
    try {
      setIsActionLoading(true);
      setError(null);
      const updated = await submissionsApi.attachResumes(selectedPackage.id);
      setSelectedPackage(updated);
      setActionSuccess('All candidate certified PDF resumes verified and attached! Package is ready for dispatch.');
      loadPackages();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to attach certified candidate resumes.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Step 27: Open & Submit Profile Dispatch Modal
  const openDispatchModal = () => {
    if (!selectedPackage) return;
    setDispatchRecipientEmail(selectedPackage.recipient_email || selectedPackage.hr_contact_email || '');
    setDispatchRecipientName(selectedPackage.recipient_name || selectedPackage.hr_contact_name || '');
    setDispatchRecipientPhone(selectedPackage.recipient_phone || selectedPackage.hr_contact_phone || '');
    setDispatchNotes('');
    setIsDispatchModalOpen(true);
  };

  const handleDispatchProfiles = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPackage) return;
    try {
      setIsActionLoading(true);
      setError(null);
      const updated = await submissionsApi.dispatchProfiles(selectedPackage.id, {
        channel: dispatchChannel,
        recipient_email: dispatchRecipientEmail,
        recipient_name: dispatchRecipientName,
        recipient_phone: dispatchRecipientPhone,
        dispatch_notes: dispatchNotes,
      });
      setIsDispatchModalOpen(false);
      setSelectedPackage(updated);
      setActionSuccess(`Profiles successfully transmitted to corporate HR! Provider Ref: ${updated.provider_reference}`);
      loadPackages();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to dispatch candidate profiles.');
    } finally {
      setIsActionLoading(false);
    }
  };

  // Step 28: Open & Submit Recruiter Acknowledgment Modal
  const openAcknowledgeModal = () => {
    if (!selectedPackage) return;
    setAckContactName(selectedPackage.hr_contact_name || '');
    setAckFeedback('');
    setAckTentativeDate('');
    setAckCallbackDate('');
    setIsAcknowledgeModalOpen(true);
  };

  const handleRecordAcknowledgement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPackage || !ackContactName.trim()) return;
    try {
      setIsActionLoading(true);
      setError(null);
      const updated = await submissionsApi.recordAcknowledgement(selectedPackage.id, {
        acknowledged_by_contact_name: ackContactName,
        acknowledgement_channel: ackChannel,
        recruiter_feedback: ackFeedback,
        tentative_interview_date: ackTentativeDate || null,
        follow_up_callback_date: ackCallbackDate || null,
      });
      setIsAcknowledgeModalOpen(false);
      setSelectedPackage(updated);
      setActionSuccess('Recruiter acknowledgment and drive schedule recorded successfully!');
      loadPackages();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to record company acknowledgment.');
    } finally {
      setIsActionLoading(false);
    }
  };

  const getStatusVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'DRAFT': return 'neutral';
      case 'READY_FOR_DISPATCH': return 'info';
      case 'DISPATCHED': return 'warning';
      case 'ACKNOWLEDGED': return 'success';
      case 'CANCELLED': return 'danger';
      default: return 'neutral';
    }
  };

  // KPI Metrics
  const totalPackages = packages.length;
  const readyPackages = packages.filter(p => p.status === 'READY_FOR_DISPATCH').length;
  const dispatchedPackages = packages.filter(p => p.status === 'DISPATCHED').length;
  const acknowledgedPackages = packages.filter(p => p.status === 'ACKNOWLEDGED').length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <span className="bg-gqt-navy text-white text-xs font-bold px-2 py-0.5 rounded tracking-wider uppercase">
              Phase 7 / Steps 24–28
            </span>
            <span className="text-xs text-gqt-neutral-500 font-medium">Candidate Submission Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-gqt-navy mt-1">
            Candidate Submissions & Profile Dispatch
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-0.5">
            Assemble verified candidate rosters, generate tamper-evident master spreadsheets, attach certified PDF resumes, and track recruiter delivery acknowledgments.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadPackages}
            className="flex items-center gap-1.5"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>

          {isStaff && (
            <Button
              variant="primary"
              size="sm"
              onClick={openCreateModal}
              className="flex items-center gap-1.5 shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Create Submission Package
            </Button>
          )}
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg flex items-start gap-3 text-rose-800 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0 text-rose-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Workflow Exception</p>
            <p className="mt-0.5">{error}</p>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-700 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {actionSuccess && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg flex items-start gap-3 text-emerald-800 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-emerald-600 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">Action Completed</p>
            <p className="mt-0.5">{actionSuccess}</p>
          </div>
          <button onClick={() => setActionSuccess(null)} className="text-emerald-500 hover:text-emerald-700 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-l-gqt-navy">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gqt-neutral-500">
              Total Packages
            </span>
            <Building2 className="w-4 h-4 text-gqt-navy" />
          </div>
          <p className="text-2xl font-bold text-gqt-navy mt-1">{totalPackages}</p>
          <span className="text-xs text-gqt-neutral-500">All candidate submission rosters</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-gqt-blue">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gqt-neutral-500">
              Ready for Dispatch
            </span>
            <FileCheck className="w-4 h-4 text-gqt-blue" />
          </div>
          <p className="text-2xl font-bold text-gqt-blue mt-1">{readyPackages}</p>
          <span className="text-xs text-gqt-neutral-500">Step 26: Resumes attached</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gqt-neutral-500">
              Dispatched to HR
            </span>
            <Send className="w-4 h-4 text-amber-600" />
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-1">{dispatchedPackages}</p>
          <span className="text-xs text-gqt-neutral-500">Step 27: Transmitted to recruiters</span>
        </Card>

        <Card className="p-4 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-gqt-neutral-500">
              Acknowledged by HR
            </span>
            <CheckCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-bold text-emerald-700 mt-1">{acknowledgedPackages}</p>
          <span className="text-xs text-gqt-neutral-500">Step 28: Receipt confirmed & dated</span>
        </Card>
      </div>

      {/* Main Split Layout: Directory (Left) & Workspace (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Package List & Filter */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="p-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-bold text-gqt-navy uppercase tracking-wider">
                Submission Packages
              </h2>
              <span className="text-xs text-gqt-neutral-500 font-medium">
                {packages.length} records
              </span>
            </div>

            {/* Filter Pills */}
            <div className="flex flex-wrap gap-1 mb-3">
              {['ALL', 'DRAFT', 'READY_FOR_DISPATCH', 'DISPATCHED', 'ACKNOWLEDGED'].map(st => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                    statusFilter === st
                      ? 'bg-gqt-navy text-white shadow-sm'
                      : 'bg-gqt-neutral-100 text-gqt-neutral-600 hover:bg-gqt-neutral-200'
                  }`}
                >
                  {st === 'ALL' ? 'All' : st.replace(/_/g, ' ')}
                </button>
              ))}
            </div>

            {/* List */}
            {isLoading ? (
              <div className="py-8 text-center text-sm text-gqt-neutral-500">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-gqt-blue mb-2" />
                Loading packages...
              </div>
            ) : packages.length === 0 ? (
              <div className="py-8 text-center text-sm text-gqt-neutral-500 bg-gqt-neutral-50 rounded-lg border border-dashed border-gqt-neutral-200 p-4">
                <Briefcase className="w-8 h-8 text-gqt-neutral-400 mx-auto mb-2" />
                <p className="font-semibold text-gqt-navy">No submission packages</p>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Create a new package to prepare candidate profiles for corporate drives.
                </p>
              </div>
            ) : (
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {packages.map(pkg => {
                  const isSelected = selectedPackage?.id === pkg.id;
                  return (
                    <div
                      key={pkg.id}
                      onClick={() => loadPackageDetails(pkg.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-gqt-blue bg-blue-50/40 shadow-sm ring-1 ring-gqt-blue'
                          : 'border-gqt-neutral-200 hover:border-gqt-neutral-300 hover:bg-gqt-neutral-50/60'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="font-semibold text-sm text-gqt-navy line-clamp-1">
                          {pkg.title}
                        </h3>
                        <StatusBadge
                          label={pkg.status.replace(/_/g, ' ')}
                          variant={getStatusVariant(pkg.status)}
                          className="text-[10px] py-0 px-2 flex-shrink-0"
                        />
                      </div>

                      <div className="mt-1 text-xs text-gqt-neutral-600 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-gqt-neutral-400" />
                        <span className="font-medium text-gqt-navy">{pkg.company_name}</span>
                        <span>•</span>
                        <span className="line-clamp-1">{pkg.job_title}</span>
                      </div>

                      <div className="mt-2 flex items-center justify-between text-[11px] text-gqt-neutral-500">
                        <span className="flex items-center gap-1">
                          <Users className="w-3 h-3 text-gqt-blue" />
                          <strong className="text-gqt-navy">{pkg.candidate_count}</strong> candidates
                        </span>
                        <span>{new Date(pkg.created_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Selected Package Workspace */}
        <div className="lg:col-span-8">
          {selectedPackage ? (
            <Card className="p-6 space-y-6">
              {/* Workspace Header */}
              <div className="border-b border-gqt-neutral-200 pb-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                        Package #{selectedPackage.id.slice(0, 8)}
                      </span>
                      <StatusBadge
                        label={selectedPackage.status.replace(/_/g, ' ')}
                        variant={getStatusVariant(selectedPackage.status)}
                      />
                    </div>
                    <h2 className="text-xl font-bold text-gqt-navy mt-1">
                      {selectedPackage.title}
                    </h2>
                  </div>

                  {/* Top Action Buttons (Steps 25-28) */}
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Step 25 Generate Master Excel */}
                    {['DRAFT', 'READY_FOR_DISPATCH'].includes(selectedPackage.status) && isStaff && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleGenerateRoster}
                        disabled={isActionLoading}
                        className="flex items-center gap-1.5 text-xs text-gqt-navy border-gqt-navy"
                      >
                        <FileSpreadsheet className="w-3.5 h-3.5 text-gqt-blue" />
                        {selectedPackage.package_hash ? 'Regenerate Excel' : 'Step 25: Generate Excel'}
                      </Button>
                    )}

                    {/* Step 25 Download Excel */}
                    {selectedPackage.has_roster_file && (
                      <a
                        href={submissionsApi.getRosterDownloadUrl(selectedPackage.id)}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg border border-emerald-300 bg-emerald-50 text-emerald-800 text-xs font-semibold hover:bg-emerald-100 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        Download Roster
                      </a>
                    )}

                    {/* Step 26 Attach Resumes */}
                    {selectedPackage.status === 'DRAFT' && isStaff && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleAttachResumes}
                        disabled={isActionLoading}
                        className="flex items-center gap-1.5 text-xs border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100"
                      >
                        <FileCheck className="w-3.5 h-3.5 text-amber-600" />
                        Step 26: Attach Resumes
                      </Button>
                    )}

                    {/* Step 27 Send Profiles to HR */}
                    {['READY_FOR_DISPATCH', 'DRAFT'].includes(selectedPackage.status) && isStaff && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={openDispatchModal}
                        disabled={isActionLoading}
                        className="flex items-center gap-1.5 text-xs shadow-sm bg-gqt-navy hover:bg-gqt-navy-dark text-white"
                      >
                        <Send className="w-3.5 h-3.5" />
                        Step 27: Send Profiles to HR
                      </Button>
                    )}

                    {/* Step 28 Record Acknowledgment */}
                    {selectedPackage.status === 'DISPATCHED' && canAcknowledge && (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={openAcknowledgeModal}
                        disabled={isActionLoading}
                        className="flex items-center gap-1.5 text-xs shadow-sm bg-emerald-600 hover:bg-emerald-700 text-white"
                      >
                        <CheckCheck className="w-3.5 h-3.5" />
                        Step 28: Record HR Acknowledgement
                      </Button>
                    )}
                  </div>
                </div>

                {/* Metadata Row */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-gqt-neutral-100 text-xs text-gqt-neutral-600">
                  <div>
                    <span className="text-gqt-neutral-400 block text-[10px] uppercase font-bold">Company Partner</span>
                    <span className="font-semibold text-gqt-navy">{selectedPackage.company_name}</span>
                  </div>
                  <div>
                    <span className="text-gqt-neutral-400 block text-[10px] uppercase font-bold">Approved Job</span>
                    <span className="font-semibold text-gqt-navy">{selectedPackage.job_title}</span>
                  </div>
                  <div>
                    <span className="text-gqt-neutral-400 block text-[10px] uppercase font-bold">HR Recipient</span>
                    <span className="font-semibold text-gqt-navy">{selectedPackage.hr_contact_name || 'Not assigned'}</span>
                  </div>
                  <div>
                    <span className="text-gqt-neutral-400 block text-[10px] uppercase font-bold">Candidate Count</span>
                    <span className="font-bold text-gqt-blue text-sm">{selectedPackage.candidate_count}</span>
                  </div>
                </div>

                {/* Cryptographic SHA-256 Digest Bar */}
                {selectedPackage.package_hash && (
                  <div className="mt-3 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-2 font-mono text-[11px] text-gqt-neutral-700 overflow-hidden">
                      <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      <span className="font-semibold text-gqt-navy">SHA-256 Roster Digest:</span>
                      <span className="truncate">{selectedPackage.package_hash}</span>
                    </div>
                    <button
                      onClick={() => navigator.clipboard.writeText(selectedPackage.package_hash)}
                      className="text-gqt-blue hover:text-gqt-navy p-1"
                      title="Copy SHA-256 hash"
                    >
                      <Copy className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>

              {/* Recruiter Acknowledgment Banner (if completed) */}
              {selectedPackage.status === 'ACKNOWLEDGED' && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                      <CheckCheck className="w-4 h-4 text-emerald-600" />
                      Receipt Acknowledged by Corporate Recruiter (Step 28)
                    </div>
                    <span className="text-xs text-emerald-700">
                      Confirmed by: <strong>{selectedPackage.acknowledged_by_contact_name}</strong> on{' '}
                      {selectedPackage.acknowledged_at ? new Date(selectedPackage.acknowledged_at).toLocaleDateString() : ''}
                    </span>
                  </div>
                  {selectedPackage.recruiter_feedback && (
                    <p className="text-xs text-emerald-900 bg-white/70 p-2.5 rounded border border-emerald-100">
                      "{selectedPackage.recruiter_feedback}"
                    </p>
                  )}
                  <div className="flex flex-wrap gap-4 text-xs text-emerald-800 pt-1">
                    {selectedPackage.tentative_interview_date && (
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3.5 h-3.5 text-emerald-600" />
                        Tentative Drive Date: <strong>{selectedPackage.tentative_interview_date}</strong>
                      </span>
                    )}
                    {selectedPackage.follow_up_callback_date && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-emerald-600" />
                        Follow-Up Callback: <strong>{selectedPackage.follow_up_callback_date}</strong>
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Candidate Roster Table */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-gqt-navy uppercase tracking-wider flex items-center gap-2">
                    <Users className="w-4 h-4 text-gqt-blue" />
                    Candidate Roster ({selectedPackage.candidates.length})
                  </h3>
                  <span className="text-xs text-gqt-neutral-500">
                    Strictly certified placement resume versions locked (Step 23 Gate)
                  </span>
                </div>

                <div className="overflow-x-auto border border-gqt-neutral-200 rounded-lg">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-gqt-navy text-white uppercase text-[10px] tracking-wider">
                      <tr>
                        <th className="py-2.5 px-3">Roll No</th>
                        <th className="py-2.5 px-3">Candidate Name</th>
                        <th className="py-2.5 px-3">Contact</th>
                        <th className="py-2.5 px-3">Department</th>
                        <th className="py-2.5 px-3 text-center">CGPA</th>
                        <th className="py-2.5 px-3 text-center">Approved Resume</th>
                        <th className="py-2.5 px-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gqt-neutral-200">
                      {selectedPackage.candidates.map((cand, idx) => (
                        <tr key={cand.id} className={idx % 2 === 0 ? 'bg-white' : 'bg-gqt-neutral-50/50'}>
                          <td className="py-2.5 px-3 font-mono font-semibold text-gqt-navy">
                            {cand.roll_number}
                          </td>
                          <td className="py-2.5 px-3 font-medium text-gqt-navy">
                            {cand.student_name}
                          </td>
                          <td className="py-2.5 px-3 text-gqt-neutral-600">
                            <div>{cand.institutional_email}</div>
                            <div className="text-[10px] text-gqt-neutral-500">{cand.phone_number}</div>
                          </td>
                          <td className="py-2.5 px-3 text-gqt-neutral-700">
                            {cand.department} ({cand.graduation_year})
                          </td>
                          <td className="py-2.5 px-3 text-center font-bold text-gqt-navy">
                            {cand.cgpa ? Number(cand.cgpa).toFixed(2) : 'N/A'}
                          </td>
                          <td className="py-2.5 px-3 text-center">
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-blue-50 text-gqt-blue text-[11px] font-semibold border border-blue-200">
                              <FileText className="w-3 h-3" />
                              v{cand.resume_version_number}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">
                            <StatusBadge
                              label={cand.status.replace(/_/g, ' ')}
                              variant={
                                cand.status === 'SUBMITTED' ? 'warning' :
                                cand.status === 'ACKNOWLEDGED' ? 'success' :
                                cand.status === 'SHORTLISTED' ? 'success' : 'neutral'
                              }
                              className="text-[10px] py-0 px-2"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Step 27 Transmission History & Logs */}
              {selectedPackage.dispatch_logs && selectedPackage.dispatch_logs.length > 0 && (
                <div className="border-t border-gqt-neutral-200 pt-4">
                  <h3 className="text-xs font-bold text-gqt-navy uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Send className="w-3.5 h-3.5 text-gqt-blue" />
                    Corporate Transmission History (Step 27)
                  </h3>
                  <div className="space-y-2">
                    {selectedPackage.dispatch_logs.map(log => (
                      <div key={log.id} className="p-3 bg-gqt-neutral-50 border border-gqt-neutral-200 rounded-lg text-xs flex items-center justify-between">
                        <div className="space-y-0.5">
                          <div className="flex items-center gap-2">
                            <span className="font-semibold text-gqt-navy">Attempt #{log.attempt_number} via {log.channel}</span>
                            <StatusBadge label={log.status} variant={log.status === 'SENT' ? 'success' : 'danger'} className="text-[10px] py-0 px-1.5" />
                          </div>
                          <p className="text-gqt-neutral-600">
                            Recipient: <strong>{log.recipient}</strong> • Provider Ref: <code className="font-mono text-gqt-blue">{log.provider_message_id}</code>
                          </p>
                        </div>
                        <div className="text-right text-gqt-neutral-500 text-[11px]">
                          <div>{new Date(log.timestamp).toLocaleString()}</div>
                          <div>By: {log.dispatched_by_name || 'System Staff'}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ) : (
            <Card className="p-12 text-center text-gqt-neutral-500">
              <Briefcase className="w-12 h-12 text-gqt-neutral-300 mx-auto mb-3" />
              <p className="font-bold text-gqt-navy text-base">Select a Submission Package</p>
              <p className="text-xs text-gqt-neutral-500 mt-1 max-w-sm mx-auto">
                Choose a candidate roster from the left directory to inspect student profiles, generate spreadsheets, and transmit packages to corporate HR.
              </p>
            </Card>
          )}
        </div>
      </div>

      {/* ==================================================================== */}
      {/* Step 24: Create Submission Package Modal */}
      {/* ==================================================================== */}
      {isCreateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <span className="text-xs font-bold text-gqt-navy uppercase tracking-wider">
                  Workflow Step 24 Gate
                </span>
                <h3 className="text-lg font-bold text-gqt-navy">
                  Prepare Candidate List & Assemble Package
                </h3>
              </div>
              <button
                onClick={() => setIsCreateModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-navy font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreatePackage} className="space-y-4">
              {/* Select Approved Job */}
              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Target Approved Job Requirement *
                </label>
                <select
                  value={selectedJobId}
                  onChange={e => handleJobSelect(e.target.value)}
                  className="w-full text-xs p-2.5 border border-gqt-neutral-300 rounded-lg focus:ring-1 focus:ring-gqt-blue"
                  required
                >
                  <option value="">-- Choose an approved job requirement --</option>
                  {approvedJobs.map(j => (
                    <option key={j.id} value={j.id}>
                      {j.company_name} — {j.title} (Approved)
                    </option>
                  ))}
                </select>
              </div>

              {/* Package Title & Notes */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Submission Package Title
                  </label>
                  <input
                    type="text"
                    value={customPackageTitle}
                    onChange={e => setCustomPackageTitle(e.target.value)}
                    placeholder="e.g. Infosys 2026 Batch - Cohort 1"
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Operational Notes
                  </label>
                  <input
                    type="text"
                    value={packageNotes}
                    onChange={e => setPackageNotes(e.target.value)}
                    placeholder="Optional placement team notes"
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  />
                </div>
              </div>

              {/* Candidate Readiness Pool Preview */}
              {isPoolLoading ? (
                <div className="py-6 text-center text-xs text-gqt-neutral-500">
                  <RefreshCw className="w-5 h-5 animate-spin mx-auto text-gqt-blue mb-2" />
                  Verifying applicant eligibility & Step 23 Placement Head certification...
                </div>
              ) : candidatePool && (
                <div className="space-y-2 border-t pt-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-gqt-navy uppercase">
                      Candidate Readiness Pool ({candidatePool.candidates.length})
                    </span>
                    <span className="text-xs text-gqt-neutral-500">
                      Selected: <strong>{selectedStudentIds.length}</strong> / {candidatePool.total_certified} certified
                    </span>
                  </div>

                  <div className="max-h-60 overflow-y-auto border border-gqt-neutral-200 rounded-lg text-xs">
                    <table className="w-full text-left border-collapse">
                      <thead className="bg-gqt-neutral-100 text-gqt-navy font-semibold text-[10px] uppercase">
                        <tr>
                          <th className="py-2 px-2.5 text-center">Select</th>
                          <th className="py-2 px-2.5">Roll No</th>
                          <th className="py-2 px-2.5">Name</th>
                          <th className="py-2 px-2.5">Branch</th>
                          <th className="py-2 px-2.5 text-center">CGPA</th>
                          <th className="py-2 px-2.5">Step 23 Readiness Gate</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gqt-neutral-200">
                        {candidatePool.candidates.map(cand => {
                          const isSelected = selectedStudentIds.includes(cand.student_id);
                          return (
                            <tr
                              key={cand.student_id}
                              className={`hover:bg-gqt-neutral-50 ${!cand.can_be_submitted ? 'opacity-50 bg-gqt-neutral-50/70' : ''}`}
                            >
                              <td className="py-2 px-2.5 text-center">
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  disabled={!cand.can_be_submitted}
                                  onChange={() => handleToggleSelectCandidate(cand.student_id)}
                                  className="rounded border-gqt-neutral-300 text-gqt-navy focus:ring-gqt-blue cursor-pointer"
                                />
                              </td>
                              <td className="py-2 px-2.5 font-mono font-semibold">{cand.roll_number}</td>
                              <td className="py-2 px-2.5 font-medium">{cand.student_name}</td>
                              <td className="py-2 px-2.5 text-gqt-neutral-600">{cand.department}</td>
                              <td className="py-2 px-2.5 text-center font-bold">{cand.cgpa ? cand.cgpa.toFixed(2) : 'N/A'}</td>
                              <td className="py-2 px-2.5">
                                {cand.has_readiness_certification ? (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                                    <ShieldCheck className="w-3 h-3 text-emerald-600" />
                                    Placement Ready (v{cand.approved_resume_version})
                                  </span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200" title="Step 23 Placement Head certification required">
                                    <Clock className="w-3 h-3 text-amber-600" />
                                    Readiness Pending
                                  </span>
                                )}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="text-[11px] text-gqt-neutral-500 italic">
                    Note: Uncertified candidates cannot be selected per authoritative Step 23 Gate rules.
                  </p>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-3 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCreateModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading || selectedStudentIds.length === 0}
                  className="bg-gqt-navy hover:bg-gqt-navy-dark text-white"
                >
                  {isActionLoading ? 'Assembling Package...' : `Assemble Package (${selectedStudentIds.length} Candidates)`}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* Step 27: Profile Dispatch Modal */}
      {/* ==================================================================== */}
      {isDispatchModalOpen && selectedPackage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <span className="text-xs font-bold text-amber-600 uppercase tracking-wider">
                  Workflow Step 27 Dispatch
                </span>
                <h3 className="text-lg font-bold text-gqt-navy">
                  Send Candidate Profiles to HR
                </h3>
              </div>
              <button
                onClick={() => setIsDispatchModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-navy font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleDispatchProfiles} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Transmission Channel
                </label>
                <select
                  value={dispatchChannel}
                  onChange={e => setDispatchChannel(e.target.value as any)}
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                >
                  <option value="EMAIL">Corporate Email Transmission</option>
                  <option value="WHATSAPP">WhatsApp Business Outreach</option>
                  <option value="PORTAL_LINK">Recruitment Portal Link</option>
                  <option value="DIRECT_HANDOFF">Direct Handoff / Campus Meeting</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Recipient HR Name
                </label>
                <input
                  type="text"
                  value={dispatchRecipientName}
                  onChange={e => setDispatchRecipientName(e.target.value)}
                  placeholder="e.g. Pooja Sharma"
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  required
                />
              </div>

              {dispatchChannel === 'EMAIL' && (
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Corporate Email Address *
                  </label>
                  <input
                    type="email"
                    value={dispatchRecipientEmail}
                    onChange={e => setDispatchRecipientEmail(e.target.value)}
                    placeholder="hr.recruitment@company.com"
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                    required
                  />
                </div>
              )}

              {dispatchChannel === 'WHATSAPP' && (
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Recipient Phone Number *
                  </label>
                  <input
                    type="text"
                    value={dispatchRecipientPhone}
                    onChange={e => setDispatchRecipientPhone(e.target.value)}
                    placeholder="+919876543210"
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                    required
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Dispatch Notes / Remarks
                </label>
                <textarea
                  value={dispatchNotes}
                  onChange={e => setDispatchNotes(e.target.value)}
                  placeholder="Add transmission remarks or cover message..."
                  rows={2}
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                />
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
                <p className="font-semibold">Transmission Confirmation</p>
                <p className="mt-0.5 text-[11px]">
                  This will dispatch <strong>{selectedPackage.candidate_count} candidate profiles</strong> and the official master roster spreadsheet to <strong>{dispatchRecipientName || selectedPackage.company_name}</strong>. Candidate statuses will transition to <code>SUBMITTED</code>.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsDispatchModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  {isActionLoading ? 'Transmitting...' : 'Confirm Profile Dispatch'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================================== */}
      {/* Step 28: Recruiter Acknowledgment Modal */}
      {/* ==================================================================== */}
      {isAcknowledgeModalOpen && selectedPackage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">
                  Workflow Step 28 Acknowledgment
                </span>
                <h3 className="text-lg font-bold text-gqt-navy">
                  Log Corporate Recruiter Receipt
                </h3>
              </div>
              <button
                onClick={() => setIsAcknowledgeModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-navy font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleRecordAcknowledgement} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Recruiter Contact Representative *
                </label>
                <input
                  type="text"
                  value={ackContactName}
                  onChange={e => setAckContactName(e.target.value)}
                  placeholder="e.g. Pooja Sharma, Talent Acquisition Lead"
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Confirmation Channel
                </label>
                <select
                  value={ackChannel}
                  onChange={e => setAckChannel(e.target.value as any)}
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                >
                  <option value="EMAIL">Email Confirmation</option>
                  <option value="PHONE_CALL">Telephone Call</option>
                  <option value="WHATSAPP">WhatsApp Message</option>
                  <option value="PORTAL">Recruiter Portal Response</option>
                  <option value="IN_PERSON">In-Person Discussion</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                  Recruiter Preliminary Feedback
                </label>
                <textarea
                  value={ackFeedback}
                  onChange={e => setAckFeedback(e.target.value)}
                  placeholder="Recruiter impressions, candidate pool feedback, or special notes..."
                  rows={2}
                  className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Tentative Interview Date
                  </label>
                  <input
                    type="date"
                    value={ackTentativeDate}
                    onChange={e => setAckTentativeDate(e.target.value)}
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gqt-navy uppercase mb-1">
                    Follow-Up Callback Date
                  </label>
                  <input
                    type="date"
                    value={ackCallbackDate}
                    onChange={e => setAckCallbackDate(e.target.value)}
                    className="w-full text-xs p-2 border border-gqt-neutral-300 rounded-lg"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setIsAcknowledgeModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  disabled={isActionLoading || !ackContactName.trim()}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white"
                >
                  {isActionLoading ? 'Saving...' : 'Record Recruiter Acknowledgment'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
