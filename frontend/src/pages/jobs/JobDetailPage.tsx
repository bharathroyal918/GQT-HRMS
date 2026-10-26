import React, { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Briefcase,
  Building2,
  CheckCircle2,
  Clock,
  FileCheck,
  XCircle,
  RotateCcw,
  Edit,
  Send,
  Archive,
  RefreshCw,
  ShieldAlert,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import {
  ChecklistItemStatus,
  JobChecklistItem,
  JobRequirementStatus,
} from '@/types/jobs';
import { Button } from '@/components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { useAuth } from '@/context/AuthContext';

export const JobDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'checklist' | 'details' | 'decisions'>('checklist');

  // Modal States
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [submitComments, setSubmitComments] = useState('');

  const [isReturnModalOpen, setIsReturnModalOpen] = useState(false);
  const [returnReason, setReturnReason] = useState('');

  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);
  const [approveComments, setApproveComments] = useState('');

  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');

  const [isReopenModalOpen, setIsReopenModalOpen] = useState(false);
  const [reopenReason, setReopenReason] = useState('');

  // Item verification state
  const [verifyingItemId, setVerifyingItemId] = useState<string | null>(null);
  const [itemRemarks, setItemRemarks] = useState<{ [key: string]: string }>({});

  const {
    data: job,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['job-detail', id],
    queryFn: () => jobsApi.getJob(id!),
    enabled: Boolean(id),
  });

  // Role permissions
  const isApprover = user?.roles.some((r) => ['ADMIN', 'PLACEMENT_HEAD'].includes(r));
  const isVerifier = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );
  const isCreatorOrStaff = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );

  // Mutations
  const submitMutation = useMutation({
    mutationFn: () => jobsApi.submitVerification(id!, submitComments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setIsSubmitModalOpen(false);
      setSubmitComments('');
    },
  });

  const verifyItemMutation = useMutation({
    mutationFn: ({
      itemId,
      status,
      remarks,
    }: {
      itemId: string;
      status: ChecklistItemStatus;
      remarks?: string;
    }) => jobsApi.verifyChecklistItem(id!, itemId, { status, remarks }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setVerifyingItemId(null);
    },
  });

  const returnMutation = useMutation({
    mutationFn: () => jobsApi.returnForCorrection(id!, returnReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setIsReturnModalOpen(false);
      setReturnReason('');
    },
  });

  const approveMutation = useMutation({
    mutationFn: () => jobsApi.approveJob(id!, approveComments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setIsApproveModalOpen(false);
      setApproveComments('');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => jobsApi.rejectJob(id!, rejectReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setIsRejectModalOpen(false);
      setRejectReason('');
    },
  });

  const reopenMutation = useMutation({
    mutationFn: () => jobsApi.reopenJob(id!, reopenReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
      setIsReopenModalOpen(false);
      setReopenReason('');
    },
  });

  const archiveMutation = useMutation({
    mutationFn: () => (job?.is_archived ? jobsApi.restoreJob(id!) : jobsApi.archiveJob(id!)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['job-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['jobs'] });
    },
  });

  if (isLoading) {
    return <LoadingState message="Loading job requirement details..." />;
  }

  if (isError || !job) {
    return (
      <ErrorState
        title="Job Requirement Not Found"
        message="The requested job requirement could not be loaded."
        onRetry={refetch}
      />
    );
  }

  const getStatusBadgeVariant = (status: JobRequirementStatus): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'VERIFIED':
        return 'info';
      case 'UNDER_REVIEW':
        return 'warning';
      case 'PENDING_VERIFICATION':
        return 'info';
      case 'CHANGES_REQUESTED':
        return 'danger';
      case 'REJECTED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getItemBadgeVariant = (status: ChecklistItemStatus): StatusVariant => {
    switch (status) {
      case 'VERIFIED':
        return 'success';
      case 'REJECTED':
        return 'danger';
      case 'NOT_APPLICABLE':
        return 'neutral';
      default:
        return 'warning';
    }
  };

  const formatSalary = (min: string | null, max: string | null, currency: string) => {
    if (!min && !max) return 'Not Disclosed';
    const curr = currency === 'INR' ? '₹' : currency;
    if (min && max) {
      const minLPA = (parseFloat(min) / 100000).toFixed(1);
      const maxLPA = (parseFloat(max) / 100000).toFixed(1);
      return `${curr}${minLPA} - ${maxLPA} LPA`;
    }
    if (min) return `${curr}${(parseFloat(min) / 100000).toFixed(1)} LPA+`;
    return `Up to ${curr}${(parseFloat(max!) / 100000).toFixed(1)} LPA`;
  };

  const progress = job.checklist_progress;
  const canApproveOpportunity = isApprover && progress?.is_complete && ['VERIFIED', 'UNDER_REVIEW'].includes(job.status);

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-gqt-neutral-600 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Requirements Directory
        </Link>
        <div className="flex items-center gap-2">
          {job.is_editable && isCreatorOrStaff && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/jobs/${job.id}/edit`)}
              leftIcon={<Edit className="w-3.5 h-3.5" />}
            >
              Edit Details
            </Button>
          )}
          {isApprover && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => archiveMutation.mutate()}
              isLoading={archiveMutation.isPending}
              leftIcon={<Archive className="w-3.5 h-3.5" />}
            >
              {job.is_archived ? 'Restore' : 'Archive'}
            </Button>
          )}
        </div>
      </div>

      {/* Main Requirement Overview Banner */}
      <Card className="border-t-4 border-t-gqt-blue">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <StatusBadge
                  variant={getStatusBadgeVariant(job.status)}
                  label={job.status.replace('_', ' ')}
                />
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-gqt-neutral-100 text-gqt-neutral-700">
                  {job.employment_type.replace('_', ' ')}
                </span>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-gqt-blue">
                  {job.work_arrangement}
                </span>
                {job.is_locked && (
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                    Locked for Creatives (Step 8)
                  </span>
                )}
              </div>

              <h1 className="text-2xl font-bold text-gqt-navy">{job.title}</h1>

              <div className="flex flex-wrap items-center gap-4 text-sm text-gqt-neutral-600 pt-1">
                <Link
                  to={`/crm/companies/${job.company}`}
                  className="font-medium text-gqt-blue hover:underline flex items-center gap-1"
                >
                  <Building2 className="w-4 h-4" />
                  {job.company_name} ({job.company_tier})
                </Link>
                <span>•</span>
                <span>Location: <strong className="text-gqt-neutral-800">{job.location}</strong></span>
                <span>•</span>
                <span>CTC: <strong className="text-gqt-neutral-800">{formatSalary(job.min_salary, job.max_salary, job.salary_currency)}</strong></span>
                <span>•</span>
                <span>Openings: <strong className="text-gqt-neutral-800">{job.openings_count}</strong></span>
              </div>

              {job.return_reason && job.status === 'CHANGES_REQUESTED' && (
                <div className="mt-3 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-2">
                  <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold">Reviewer Change Request:</span> {job.return_reason}
                  </div>
                </div>
              )}
            </div>

            {/* Checklist Progress Gauge */}
            <div className="bg-gqt-neutral-50 p-4 rounded-xl border border-gqt-neutral-200/80 min-w-[260px] space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-gqt-neutral-600 uppercase tracking-wider">
                <span>5-Point Verification</span>
                <span className="text-gqt-blue">{progress?.percentage || 0}%</span>
              </div>
              <div className="w-full bg-gqt-neutral-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    progress?.is_complete ? 'bg-emerald-500' : 'bg-gqt-blue'
                  }`}
                  style={{ width: `${progress?.percentage || 0}%` }}
                />
              </div>
              <div className="text-xs text-gqt-neutral-500 flex items-center justify-between">
                <span>
                  {progress?.verified_mandatory || 0} of {progress?.total_mandatory || 5} points passed
                </span>
                {progress?.is_complete ? (
                  <span className="text-emerald-600 font-semibold flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                  </span>
                ) : (
                  <span className="text-amber-600 font-medium flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" /> Action Required
                  </span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Primary Lifecycle Action Toolbar */}
      <Card>
        <CardContent className="p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">
              Current Stage:
            </span>
            <span className="text-sm font-bold text-gqt-navy">
              {job.status === 'DRAFT' && 'Step 5: Job Description Ingestion'}
              {['PENDING_VERIFICATION', 'UNDER_REVIEW', 'CHANGES_REQUESTED'].includes(job.status) &&
                'Step 6: Checklist Audit & Verification'}
              {job.status === 'VERIFIED' && 'Step 6 Verified — Ready for Step 7 Sign-Off'}
              {job.status === 'APPROVED' && 'Step 7 Complete — Approved for Creative Design (Step 8)'}
              {job.status === 'REJECTED' && 'Opportunity Rejected'}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Submit for Verification */}
            {['DRAFT', 'CHANGES_REQUESTED'].includes(job.status) && isCreatorOrStaff && (
              <Button
                variant="primary"
                onClick={() => setIsSubmitModalOpen(true)}
                leftIcon={<Send className="w-4 h-4" />}
              >
                Submit for Verification (Step 6)
              </Button>
            )}

            {/* Return for Correction */}
            {['PENDING_VERIFICATION', 'UNDER_REVIEW', 'VERIFIED'].includes(job.status) && isVerifier && (
              <Button
                variant="outline"
                onClick={() => setIsReturnModalOpen(true)}
                leftIcon={<RotateCcw className="w-4 h-4 text-amber-600" />}
              >
                Return for Correction
              </Button>
            )}

            {/* Reject Opportunity */}
            {['PENDING_VERIFICATION', 'UNDER_REVIEW', 'VERIFIED'].includes(job.status) && isApprover && (
              <Button
                variant="danger"
                onClick={() => setIsRejectModalOpen(true)}
                leftIcon={<XCircle className="w-4 h-4" />}
              >
                Reject Opportunity
              </Button>
            )}

            {/* Approve Opportunity (Placement Head Sign-Off) */}
            {['VERIFIED', 'UNDER_REVIEW'].includes(job.status) && isApprover && (
              <Button
                variant="primary"
                disabled={!canApproveOpportunity}
                onClick={() => setIsApproveModalOpen(true)}
                className={canApproveOpportunity ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
                leftIcon={<CheckCircle2 className="w-4 h-4" />}
                title={
                  !canApproveOpportunity
                    ? 'All 5 mandatory checklist items must be verified before approval can be signed off'
                    : 'Approve this hiring opportunity and lock for creatives'
                }
              >
                Approve Opportunity (Step 7)
              </Button>
            )}

            {/* Reopen Opportunity */}
            {['APPROVED', 'REJECTED'].includes(job.status) && isApprover && (
              <Button
                variant="outline"
                onClick={() => setIsReopenModalOpen(true)}
                leftIcon={<RefreshCw className="w-4 h-4 text-gqt-blue" />}
              >
                Reopen for Audit
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Tabs Navigation */}
      <div className="border-b border-gqt-neutral-200 flex gap-6">
        <button
          onClick={() => setActiveTab('checklist')}
          className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
            activeTab === 'checklist'
              ? 'border-gqt-blue text-gqt-blue'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-800'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          5-Point Verification Checklist (Step 6)
          <span className="text-xs px-2 py-0.5 rounded-full bg-gqt-neutral-100 text-gqt-neutral-700">
            {progress?.verified_mandatory || 0}/{progress?.total_mandatory || 5}
          </span>
        </button>

        <button
          onClick={() => setActiveTab('details')}
          className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
            activeTab === 'details'
              ? 'border-gqt-blue text-gqt-blue'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-800'
          }`}
        >
          <Briefcase className="w-4 h-4" />
          Full Job Specifications (Step 5)
        </button>

        <button
          onClick={() => setActiveTab('decisions')}
          className={`pb-3 text-sm font-semibold transition-colors border-b-2 flex items-center gap-2 ${
            activeTab === 'decisions'
              ? 'border-gqt-blue text-gqt-blue'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-neutral-800'
          }`}
        >
          <Clock className="w-4 h-4" />
          Audit & Decision History ({job.decisions?.length || 0})
        </button>
      </div>

      {/* TAB 1: 5-Point Verification Checklist (Step 6) */}
      {activeTab === 'checklist' && (
        <div className="space-y-4">
          <div className="bg-blue-50/60 p-4 rounded-xl border border-blue-200/80 text-xs text-gqt-navy flex items-start gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-gqt-blue shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Authoritative Step 6 Verification Gate:</span>
              <p className="mt-0.5 text-gqt-neutral-600">
                Placement Officers verify all 5 institutional criteria. Every mandatory item must evaluate to{' '}
                <strong className="text-emerald-700">Verified & Passed</strong> before the Placement Head can sign off and lock the opportunity for Phase 4 design creatives.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {job.checklist_items?.map((item: JobChecklistItem) => {
              const isVerifying = verifyingItemId === item.id;

              return (
                <Card key={item.id} className="overflow-hidden">
                  <div className="p-4 sm:p-5 flex flex-col md:flex-row md:items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-gqt-neutral-100 text-gqt-neutral-700">
                          {item.item_code}
                        </span>
                        <StatusBadge
                          variant={getItemBadgeVariant(item.status)}
                          label={item.status.replace('_', ' ')}
                        />
                        {item.is_mandatory && (
                          <span className="text-xs font-semibold text-rose-600">
                            * Mandatory
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-bold text-gqt-navy">{item.title}</h3>
                      <p className="text-sm text-gqt-neutral-600">{item.description}</p>

                      {item.remarks && (
                        <div className="mt-2 text-xs bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200/60 text-gqt-neutral-700">
                          <span className="font-semibold text-gqt-navy">Reviewer Remarks:</span> {item.remarks}
                        </div>
                      )}

                      {item.verified_by_name && (
                        <div className="text-xs text-gqt-neutral-400 pt-1">
                          Verified by <strong className="text-gqt-neutral-600">{item.verified_by_name}</strong> on{' '}
                          {item.verified_at ? new Date(item.verified_at).toLocaleString('en-IN') : '-'}
                        </div>
                      )}
                    </div>

                    {/* Verification Actions */}
                    {isVerifier && !job.is_locked && (
                      <div className="flex flex-col sm:flex-row items-end sm:items-center gap-2 shrink-0">
                        {isVerifying ? (
                          <div className="space-y-2 bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200">
                            <input
                              type="text"
                              placeholder="Enter audit remarks or feedback..."
                              value={itemRemarks[item.id] || ''}
                              onChange={(e) =>
                                setItemRemarks({ ...itemRemarks, [item.id]: e.target.value })
                              }
                              className="w-full text-xs px-2.5 py-1.5 border border-gqt-neutral-300 rounded focus:outline-none focus:ring-1 focus:ring-gqt-blue"
                            />
                            <div className="flex gap-1.5 justify-end">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => setVerifyingItemId(null)}
                              >
                                Cancel
                              </Button>
                              <Button
                                size="sm"
                                variant="danger"
                                onClick={() =>
                                  verifyItemMutation.mutate({
                                    itemId: item.id,
                                    status: 'REJECTED',
                                    remarks: itemRemarks[item.id],
                                  })
                                }
                                isLoading={verifyItemMutation.isPending}
                              >
                                Fails Criteria
                              </Button>
                              <Button
                                size="sm"
                                variant="primary"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() =>
                                  verifyItemMutation.mutate({
                                    itemId: item.id,
                                    status: 'VERIFIED',
                                    remarks: itemRemarks[item.id],
                                  })
                                }
                                isLoading={verifyItemMutation.isPending}
                              >
                                Verify & Pass
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => {
                                setVerifyingItemId(item.id);
                                setItemRemarks({ ...itemRemarks, [item.id]: item.remarks || '' });
                              }}
                            >
                              Update Decision
                            </Button>
                            {item.status !== 'VERIFIED' && (
                              <Button
                                size="sm"
                                variant="primary"
                                className="bg-emerald-600 hover:bg-emerald-700"
                                onClick={() =>
                                  verifyItemMutation.mutate({
                                    itemId: item.id,
                                    status: 'VERIFIED',
                                    remarks: 'Criteria verified & approved.',
                                  })
                                }
                                isLoading={verifyItemMutation.isPending}
                                leftIcon={<CheckCircle2 className="w-3.5 h-3.5" />}
                              >
                                Quick Verify
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: Full Job Specifications (Step 5) */}
      {activeTab === 'details' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">1. Role Responsibilities & Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wide">
                  Job Description
                </h4>
                <p className="text-sm text-gqt-neutral-800 whitespace-pre-line mt-1">
                  {job.job_description}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wide">
                  Technical & Functional Skills Required
                </h4>
                <p className="text-sm text-gqt-neutral-800 whitespace-pre-line mt-1 font-mono bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200/60">
                  {job.skills_required}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">2. Compensation & Service Agreement</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Annual CTC</h4>
                <p className="text-sm font-semibold text-gqt-navy mt-0.5">
                  {formatSalary(job.min_salary, job.max_salary, job.salary_currency)}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Service Agreement / Bond</h4>
                <p className="text-sm font-semibold text-gqt-navy mt-0.5">
                  {job.has_bond ? `Yes — ${job.bond_details || 'Details in offer'}` : 'No Service Agreement Required'}
                </p>
              </div>

              {job.salary_breakup && (
                <div className="md:col-span-2">
                  <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Breakup & Stipend Details</h4>
                  <p className="text-sm text-gqt-neutral-700 whitespace-pre-line mt-0.5">
                    {job.salary_breakup}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold">3. Academic Criteria & Selection Stages</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Minimum CGPA Cutoff</h4>
                <p className="text-sm font-semibold text-gqt-navy mt-0.5">
                  {job.min_cgpa ? `${job.min_cgpa} / 10.0` : 'No CGPA Cutoff'}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Registration Cutoff Deadline</h4>
                <p className="text-sm font-semibold text-rose-600 mt-0.5">
                  {new Date(job.registration_deadline).toLocaleString('en-IN')}
                </p>
              </div>

              {job.eligibility_criteria && (
                <div className="md:col-span-2">
                  <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Degree & Academic Criteria</h4>
                  <p className="text-sm text-gqt-neutral-700 whitespace-pre-line mt-0.5">
                    {job.eligibility_criteria}
                  </p>
                </div>
              )}

              {job.hiring_process && (
                <div className="md:col-span-2">
                  <h4 className="text-xs font-semibold text-gqt-neutral-500 uppercase">Evaluation & Selection Rounds</h4>
                  <p className="text-sm text-gqt-neutral-700 whitespace-pre-line mt-0.5">
                    {job.hiring_process}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 3: Decision & Audit History (Step 7) */}
      {activeTab === 'decisions' && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">Decision & Approval Audit Log</CardTitle>
          </CardHeader>
          <CardContent>
            {!job.decisions || job.decisions.length === 0 ? (
              <p className="text-sm text-gqt-neutral-500 py-4 text-center">
                No lifecycle decisions recorded yet.
              </p>
            ) : (
              <div className="relative border-l-2 border-gqt-neutral-200 ml-3 space-y-6 py-2">
                {job.decisions.map((dec) => (
                  <div key={dec.id} className="relative pl-6">
                    <span className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-gqt-blue" />
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold px-2 py-0.5 rounded bg-blue-50 text-gqt-blue">
                          {dec.decision}
                        </span>
                        <span className="text-xs text-gqt-neutral-400">
                          {new Date(dec.created_at).toLocaleString('en-IN')}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-gqt-navy">
                        By {dec.actor_name} {dec.actor_role && `(${dec.actor_role})`}
                      </div>
                      {dec.comments && (
                        <p className="text-sm text-gqt-neutral-600 bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200/60 mt-1">
                          {dec.comments}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modal: Submit for Verification */}
      {isSubmitModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gqt-navy">Submit for Verification (Step 6)</h3>
            <p className="text-sm text-gqt-neutral-600">
              This will transition the requirement to <strong>Pending Verification</strong> and notify the Placement team to audit the 5-point checklist.
            </p>
            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase mb-1">
                Submission Notes (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Any specific instructions for the verification team..."
                value={submitComments}
                onChange={(e) => setSubmitComments(e.target.value)}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setIsSubmitModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={() => submitMutation.mutate()}
                isLoading={submitMutation.isPending}
              >
                Confirm Submission
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Return for Correction */}
      {isReturnModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gqt-navy">Return for Correction</h3>
            <p className="text-sm text-gqt-neutral-600">
              Specify what criteria failed or requires adjustment. The creator will be notified to revise the job details.
            </p>
            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase mb-1">
                Reason / Actionable Feedback *
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Salary breakup is missing variable components; corporate website is under maintenance..."
                value={returnReason}
                onChange={(e) => setReturnReason(e.target.value)}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setIsReturnModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                disabled={!returnReason.trim()}
                onClick={() => returnMutation.mutate()}
                isLoading={returnMutation.isPending}
              >
                Return to Creator
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Approve Opportunity (Step 7) */}
      {isApproveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Approve Hiring Opportunity (Step 7)
            </h3>
            <p className="text-sm text-gqt-neutral-600">
              Formal Placement Head sign-off certifying that all 5 verification criteria have been satisfied. This action <strong>locks</strong> the job details and advances it to Phase 4 (Creative Design Studio).
            </p>
            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase mb-1">
                Approval Remarks / Sign-off Comments
              </label>
              <textarea
                rows={3}
                placeholder="e.g. Verified with HR Director. Approved for campus broadcast."
                value={approveComments}
                onChange={(e) => setApproveComments(e.target.value)}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setIsApproveModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                className="bg-emerald-600 hover:bg-emerald-700"
                onClick={() => approveMutation.mutate()}
                isLoading={approveMutation.isPending}
              >
                Sign & Lock Opportunity
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Reject Opportunity */}
      {isRejectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-rose-800 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-rose-600" />
              Reject Job Opportunity
            </h3>
            <p className="text-sm text-gqt-neutral-600">
              Formally decline this corporate hiring requirement. A documented rejection reason is mandatory for institutional audit records.
            </p>
            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase mb-1">
                Rejection Reason *
              </label>
              <textarea
                rows={3}
                placeholder="Document why this opportunity is being declined..."
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setIsRejectModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="danger"
                disabled={!rejectReason.trim()}
                onClick={() => rejectMutation.mutate()}
                isLoading={rejectMutation.isPending}
              >
                Confirm Rejection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Reopen Opportunity */}
      {isReopenModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-xl">
            <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-gqt-blue" />
              Reopen Requirement for Audit
            </h3>
            <p className="text-sm text-gqt-neutral-600">
              Authorized reopening moves the requirement back to <strong>Under Review</strong>, allowing criteria to be re-audited or updated.
            </p>
            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-700 uppercase mb-1">
                Reopening Justification *
              </label>
              <textarea
                rows={3}
                placeholder="Explain the justification for reopening..."
                value={reopenReason}
                onChange={(e) => setReopenReason(e.target.value)}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setIsReopenModalOpen(false)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                disabled={!reopenReason.trim()}
                onClick={() => reopenMutation.mutate()}
                isLoading={reopenMutation.isPending}
              >
                Reopen Requirement
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
