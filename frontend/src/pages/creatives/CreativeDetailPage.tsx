import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Palette,
  ArrowLeft,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileCheck,
  Upload,
  UserCheck,
  RotateCcw,
  ShieldAlert,
  Download,
  ExternalLink,
  MessageSquare,
  History,
  Info,
  X,
  FileText,
  Briefcase,
} from 'lucide-react';
import { creativesApi } from '@/api/creativesApi';
import type {
  CreativeAssetVersion,
  CreativeChecklistItem,
  ChecklistItemCode,
  ChecklistItemStatus,
} from '@/types/creatives';
import { Button } from '@/components/common/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { useAuth } from '@/context/AuthContext';

export const CreativeDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'checklist' | 'brief' | 'history'>('checklist');
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);

  // Modals state
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isCorrectionModalOpen, setIsCorrectionModalOpen] = useState(false);
  const [isApproveModalOpen, setIsApproveModalOpen] = useState(false);
  const [isRejectModalOpen, setIsRejectModalOpen] = useState(false);

  // Form states
  const [designerIdInput, setDesignerIdInput] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [designerNotesInput, setDesignerNotesInput] = useState('');
  const [correctionFeedback, setCorrectionFeedback] = useState('');
  const [approveComments, setApproveComments] = useState('');
  const [rejectionReason, setRejectionReason] = useState('');
  const [itemRemarks, setItemRemarks] = useState<Record<string, string>>({});

  const {
    data: creativeReq,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['creative-request', id],
    queryFn: () => creativesApi.getCreativeRequest(id!),
    enabled: !!id,
  });

  const canAssign = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );

  const canVerifyChecklist = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );

  const canApprove = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD'].includes(r)
  );

  const isAssignedDesigner =
    user?.id === creativeReq?.assigned_designer?.id ||
    user?.roles.some((r) => ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r));

  // Determine active version
  const versions = creativeReq?.versions || [];
  const currentVersion =
    versions.find((v: CreativeAssetVersion) => v.id === selectedVersionId) ||
    versions[0] ||
    null;

  // Mutations
  const assignMutation = useMutation({
    mutationFn: (designerId: string) => creativesApi.assignDesigner(id!, designerId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
      setIsAssignModalOpen(false);
    },
  });

  const uploadMutation = useMutation({
    mutationFn: (formData: FormData) => creativesApi.uploadAssetVersion(id!, formData),
    onSuccess: (newVersion) => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
      setSelectedVersionId(newVersion.id);
      setIsUploadModalOpen(false);
      setUploadFile(null);
      setDesignerNotesInput('');
    },
  });

  const verifyItemMutation = useMutation({
    mutationFn: ({
      versionId,
      itemCode,
      status,
      remarks,
    }: {
      versionId: string;
      itemCode: ChecklistItemCode;
      status: ChecklistItemStatus;
      remarks?: string;
    }) => creativesApi.verifyChecklistItem(id!, versionId, itemCode, { status, remarks }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
    },
  });

  const returnCorrectionMutation = useMutation({
    mutationFn: ({ versionId, feedback }: { versionId: string; feedback: string }) =>
      creativesApi.returnForCorrection(id!, versionId, feedback),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
      setIsCorrectionModalOpen(false);
      setCorrectionFeedback('');
    },
  });

  const approveMutation = useMutation({
    mutationFn: ({ versionId, comments }: { versionId: string; comments: string }) =>
      creativesApi.approveAssetVersion(id!, versionId, comments),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
      setIsApproveModalOpen(false);
      setApproveComments('');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ versionId, reason }: { versionId: string; reason: string }) =>
      creativesApi.rejectAssetVersion(id!, versionId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['creative-request', id] });
      setIsRejectModalOpen(false);
      setRejectionReason('');
    },
  });

  if (isLoading) {
    return <LoadingState message="Loading creative production workspace..." />;
  }

  if (isError || !creativeReq) {
    return (
      <ErrorState
        title="Creative Request Not Found"
        message="The requested creative production brief could not be located."
        onRetry={() => refetch()}
      />
    );
  }

  const getStatusBadgeVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'REVIEW_PENDING':
      case 'IN_REVIEW':
        return 'info';
      case 'IN_PRODUCTION':
      case 'ASSIGNED':
        return 'warning';
      case 'CHANGES_REQUESTED':
      case 'REJECTED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getChecklistItemBadgeVariant = (status: ChecklistItemStatus): StatusVariant => {
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

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('designer_notes', designerNotesInput);
    formData.append('deliverable_type', creativeReq.deliverable_type);

    uploadMutation.mutate(formData);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* Top Navigation */}
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate('/creatives')}
          className="text-slate-600 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back to Directory
        </Button>
      </div>

      {/* Main Header Card */}
      <Card className="border-t-4 border-t-[#001B4D]">
        <CardContent className="p-6 space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <StatusBadge
                  variant={getStatusBadgeVariant(creativeReq.status)}
                  label={creativeReq.status_display}
                />
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                  {creativeReq.deliverable_type_display}
                </span>
                <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                  Priority: {creativeReq.priority}
                </span>
                {creativeReq.is_locked && (
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">
                    Step 9 Signed Off
                  </span>
                )}
              </div>
              <h1 className="text-2xl font-bold text-slate-900">{creativeReq.title}</h1>
              <div className="text-sm text-slate-600 flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-slate-800">{creativeReq.company_name}</span>
                <span>•</span>
                <span>{creativeReq.job_title}</span>
                {creativeReq.production_deadline && (
                  <>
                    <span>•</span>
                    <span className="text-amber-700 flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      Deadline: {new Date(creativeReq.production_deadline).toLocaleDateString()}
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center gap-2 flex-wrap">
              {canAssign && !creativeReq.is_locked && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsAssignModalOpen(true)}
                  className="flex items-center gap-1.5 border-slate-300 text-slate-700"
                >
                  <UserCheck className="w-4 h-4 text-[#005BBB]" />
                  {creativeReq.assigned_designer ? 'Reassign Designer' : 'Assign Designer'}
                </Button>
              )}

              {isAssignedDesigner && !creativeReq.is_locked && (
                <Button
                  size="sm"
                  onClick={() => setIsUploadModalOpen(true)}
                  className="bg-[#001B4D] hover:bg-[#002875] text-white flex items-center gap-1.5"
                >
                  <Upload className="w-4 h-4" />
                  Upload New Version
                </Button>
              )}

              {canVerifyChecklist && currentVersion && !currentVersion.is_approved && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsCorrectionModalOpen(true)}
                  className="border-amber-300 text-amber-800 hover:bg-amber-50 flex items-center gap-1.5"
                >
                  <RotateCcw className="w-4 h-4 text-amber-600" />
                  Return for Changes
                </Button>
              )}

              {canApprove && currentVersion && !currentVersion.is_approved && (
                <Button
                  size="sm"
                  onClick={() => setIsApproveModalOpen(true)}
                  disabled={!currentVersion.checklist_progress.all_verified}
                  className={`flex items-center gap-1.5 text-white ${
                    currentVersion.checklist_progress.all_verified
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-slate-400 cursor-not-allowed'
                  }`}
                  title={
                    !currentVersion.checklist_progress.all_verified
                      ? 'Sign-off is locked: All 4 checklist criteria must be verified first'
                      : 'Step 9 Placement Head Sign-off'
                  }
                >
                  <CheckCircle2 className="w-4 h-4" />
                  Sign Off & Approve (Step 9)
                </Button>
              )}

              {canApprove && currentVersion && !currentVersion.is_approved && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsRejectModalOpen(true)}
                  className="border-red-300 text-red-700 hover:bg-red-50 flex items-center gap-1.5"
                >
                  <ShieldAlert className="w-4 h-4 text-red-600" />
                  Reject
                </Button>
              )}
            </div>
          </div>

          {/* Designer and Requester Info */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <div>
              <span className="font-semibold text-slate-700">Assigned Designer:</span>{' '}
              {creativeReq.assigned_designer ? (
                <span className="text-slate-900 font-medium">{creativeReq.assigned_designer.full_name} ({creativeReq.assigned_designer.email})</span>
              ) : (
                <span className="text-amber-600 font-medium">Unassigned</span>
              )}
            </div>
            <div>
              <span className="font-semibold text-slate-700">Requester:</span> {creativeReq.created_by?.full_name || 'Placement Officer'}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs Navigation */}
      <div className="flex border-b border-slate-200 gap-8 text-sm font-semibold">
        <button
          onClick={() => setActiveTab('checklist')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'checklist'
              ? 'border-[#005BBB] text-[#001B4D]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          4-Point Design Verification (Step 9)
          {currentVersion && (
            <span className="ml-1 px-2 py-0.5 rounded-full text-xs bg-slate-100 text-slate-700">
              {currentVersion.checklist_progress.verified}/4
            </span>
          )}
        </button>

        <button
          onClick={() => setActiveTab('brief')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'brief'
              ? 'border-[#005BBB] text-[#001B4D]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Info className="w-4 h-4" />
          Creative Brief & Job Specs (Step 8)
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeTab === 'history'
              ? 'border-[#005BBB] text-[#001B4D]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <History className="w-4 h-4" />
          Revisions & Decisions ({versions.length})
        </button>
      </div>

      {/* TAB 1: 4-Point Design Verification Checklist */}
      {activeTab === 'checklist' && (
        <div className="space-y-6">
          {!currentVersion ? (
            <Card>
              <CardContent className="p-8 text-center space-y-3">
                <Palette className="w-12 h-12 text-slate-300 mx-auto" />
                <h3 className="text-base font-bold text-slate-800">No Asset Version Uploaded Yet</h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto">
                  The assigned graphic designer has not uploaded an asset revision. Once an asset is uploaded, the authoritative 4-point design verification checklist will activate.
                </p>
                {isAssignedDesigner && (
                  <Button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="bg-[#001B4D] hover:bg-[#002875] text-white mt-2"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Upload Draft v1
                  </Button>
                )}
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-6">
              {/* Asset Version Control Bar */}
              <Card className="bg-slate-50/50">
                <CardContent className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                      Asset Revision:
                    </span>
                    <select
                      value={currentVersion.id}
                      onChange={(e) => setSelectedVersionId(e.target.value)}
                      className="px-3 py-1.5 text-sm font-semibold border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                    >
                      {versions.map((v: CreativeAssetVersion) => (
                        <option key={v.id} value={v.id}>
                          Version {v.version_number} — {v.status_display} ({v.file_name})
                        </option>
                      ))}
                    </select>
                    <StatusBadge
                      variant={getStatusBadgeVariant(currentVersion.status)}
                      label={currentVersion.status_display}
                    />
                  </div>

                  <div className="flex items-center gap-3 text-xs text-slate-600">
                    {currentVersion.width_px && currentVersion.height_px && (
                      <span>{currentVersion.width_px} × {currentVersion.height_px} px</span>
                    )}
                    <span>{(currentVersion.file_size_bytes / 1024).toFixed(1)} KB</span>
                    <a
                      href={creativesApi.getAssetFileUrl(id!, currentVersion.id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 font-semibold text-[#005BBB] hover:text-[#001B4D] ml-2"
                    >
                      <Download className="w-4 h-4" />
                      Download Asset
                    </a>
                  </div>
                </CardContent>
              </Card>

              {/* Version Status Alerts */}
              {currentVersion.is_approved && (
                <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-lg text-sm text-emerald-900 flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold">Placement Head Sign-Off Certified (Step 9 Passed)</p>
                    <p className="text-xs text-emerald-800 mt-0.5">
                      This promotional asset has passed all 4 mandatory verification checks and was approved by{' '}
                      <span className="font-semibold">{currentVersion.approved_by?.full_name}</span> on{' '}
                      {currentVersion.approved_at && new Date(currentVersion.approved_at).toLocaleString()}. It is now eligible for student publication broadcast (Step 10).
                    </p>
                  </div>
                </div>
              )}

              {currentVersion.status === 'CHANGES_REQUESTED' && (
                <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-sm text-red-900 flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-bold">Revisions Required for Version {currentVersion.version_number}</p>
                    <p className="text-xs text-red-800 mt-0.5 font-medium">Feedback: {currentVersion.rejection_reason}</p>
                  </div>
                </div>
              )}

              {/* 4-Point Checklist Card */}
              <Card>
                <CardHeader className="pb-3 border-b border-slate-100 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                      <FileCheck className="w-5 h-5 text-[#005BBB]" />
                      Authoritative 4-Point Design Verification Checklist
                    </CardTitle>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Source: `HRMS - Complete Workflow` Step 9. All 4 checks must evaluate to VERIFIED before Placement Head sign-off.
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-semibold text-slate-600">
                      Progress: {currentVersion.checklist_progress.verified} / 4 Verified
                    </span>
                    <div className="w-32 bg-slate-200 rounded-full h-2 mt-1">
                      <div
                        className={`h-2 rounded-full ${
                          currentVersion.checklist_progress.all_verified ? 'bg-emerald-600' : 'bg-[#005BBB]'
                        }`}
                        style={{ width: `${currentVersion.checklist_progress.percent}%` }}
                      />
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="divide-y divide-slate-100 p-0">
                  {currentVersion.checklist_items.map((item: CreativeChecklistItem) => {
                    const remarksVal = itemRemarks[item.item_code] ?? item.remarks;
                    const isImmutable = currentVersion.is_approved;

                    return (
                      <div key={item.id} className="p-4 sm:p-5 space-y-3">
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                          <div className="space-y-1 max-w-2xl">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-bold text-slate-900">{item.title}</span>
                              <StatusBadge
                                variant={getChecklistItemBadgeVariant(item.status)}
                                label={item.status}
                              />
                            </div>
                            <p className="text-xs text-slate-600">{item.description}</p>
                            {item.verified_by && (
                              <p className="text-xs text-slate-400">
                                Audited by {item.verified_by.full_name} on{' '}
                                {item.verified_at && new Date(item.verified_at).toLocaleString()}
                              </p>
                            )}
                          </div>

                          {/* Verification Buttons */}
                          {canVerifyChecklist && !isImmutable && (
                            <div className="flex items-center gap-2 self-start sm:self-center">
                              <Button
                                size="sm"
                                variant={item.status === 'VERIFIED' ? 'primary' : 'outline'}
                                onClick={() =>
                                  verifyItemMutation.mutate({
                                    versionId: currentVersion.id,
                                    itemCode: item.item_code,
                                    status: 'VERIFIED',
                                    remarks: remarksVal,
                                  })
                                }
                                disabled={verifyItemMutation.isPending}
                                className={
                                  item.status === 'VERIFIED'
                                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white text-xs h-8'
                                    : 'border-slate-300 text-slate-700 hover:bg-emerald-50 text-xs h-8'
                                }
                              >
                                Pass
                              </Button>
                              <Button
                                size="sm"
                                variant={item.status === 'REJECTED' ? 'danger' : 'outline'}
                                onClick={() =>
                                  verifyItemMutation.mutate({
                                    versionId: currentVersion.id,
                                    itemCode: item.item_code,
                                    status: 'REJECTED',
                                    remarks: remarksVal,
                                  })
                                }
                                disabled={verifyItemMutation.isPending}
                                className={
                                  item.status === 'REJECTED'
                                    ? 'bg-red-600 text-white text-xs h-8'
                                    : 'border-slate-300 text-slate-700 hover:bg-red-50 text-xs h-8'
                                }
                              >
                                Fail
                              </Button>
                            </div>
                          )}
                        </div>

                        {/* Remarks Input */}
                        {!isImmutable && canVerifyChecklist ? (
                          <div className="pt-1">
                            <input
                              type="text"
                              placeholder="Add verifier remarks or correction feedback for this point..."
                              value={remarksVal}
                              onChange={(e) =>
                                setItemRemarks((prev) => ({
                                  ...prev,
                                  [item.item_code]: e.target.value,
                                }))
                              }
                              className="w-full px-3 py-1.5 text-xs border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-[#005BBB]"
                            />
                          </div>
                        ) : item.remarks ? (
                          <div className="text-xs bg-slate-50 p-2 rounded text-slate-700 italic">
                            Verifier Remarks: &ldquo;{item.remarks}&rdquo;
                          </div>
                        ) : null}
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Creative Brief & Approved Job Spec (Step 8) */}
      {activeTab === 'brief' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#005BBB]" />
                Creative Brief & Copy
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4 text-sm">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Format</span>
                <p className="font-semibold text-slate-900">{creativeReq.deliverable_type_display}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Target Cohort</span>
                <p className="text-slate-800">{creativeReq.target_audience || 'All Eligible Campus Freshers'}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Instructions & Copy</span>
                <pre className="text-xs bg-slate-50 p-3 rounded-lg border border-slate-200 whitespace-pre-wrap font-sans text-slate-800 mt-1">
                  {creativeReq.brief}
                </pre>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs pt-2">
                <div>
                  <span className="font-semibold text-slate-500">Contact Email:</span>{' '}
                  <span className="text-slate-800">{creativeReq.contact_email || 'placements@gqt.edu'}</span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500">Contact Phone:</span>{' '}
                  <span className="text-slate-800">{creativeReq.contact_phone || 'TBA'}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-[#005BBB]" />
                Approved Job Specifications (Step 5 Reference)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3 text-sm">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Employer</span>
                <p className="font-bold text-slate-900">{creativeReq.company_name}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Role Title</span>
                <p className="text-slate-800 font-semibold">{creativeReq.job_title}</p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Salary Package</span>
                <p className="text-slate-800">
                  {creativeReq.job_min_salary && creativeReq.job_max_salary
                    ? `${creativeReq.job_min_salary} - ${creativeReq.job_max_salary} LPA`
                    : 'Disclosed during interview'}
                </p>
              </div>
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Academic Eligibility</span>
                <p className="text-xs text-slate-700 bg-slate-50 p-2 rounded border border-slate-100 mt-0.5">
                  {creativeReq.job_eligibility}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                <div>
                  <span className="font-semibold text-slate-500">Drive Date:</span>{' '}
                  <span className="text-slate-800">
                    {creativeReq.job_interview_date ? new Date(creativeReq.job_interview_date).toLocaleDateString() : 'TBA'}
                  </span>
                </div>
                <div>
                  <span className="font-semibold text-slate-500">Cutoff:</span>{' '}
                  <span className="text-slate-800">
                    {new Date(creativeReq.job_deadline).toLocaleDateString()}
                  </span>
                </div>
              </div>
              {creativeReq.registration_link && (
                <div className="pt-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Verified Registration Link</span>
                  <a
                    href={creativeReq.registration_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-[#005BBB] hover:underline flex items-center gap-1 mt-0.5 break-all"
                  >
                    {creativeReq.registration_link}
                    <ExternalLink className="w-3 h-3 flex-shrink-0" />
                  </a>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* TAB 3: Version History & Decision Audit */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <History className="w-5 h-5 text-[#005BBB]" />
                Asset Revision History ({versions.length} versions)
              </CardTitle>
            </CardHeader>
            <CardContent className="divide-y divide-slate-100 p-0">
              {versions.length === 0 ? (
                <p className="p-4 text-xs text-slate-500 italic">No asset versions uploaded yet.</p>
              ) : (
                versions.map((ver: CreativeAssetVersion) => (
                  <div key={ver.id} className="p-4 flex items-center justify-between">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-900 text-sm">Version {ver.version_number}</span>
                        <StatusBadge
                          variant={getStatusBadgeVariant(ver.status)}
                          label={ver.status}
                        />
                        <span className="text-xs text-slate-500 font-mono">[{ver.sha256_hash.slice(0, 8)}...]</span>
                      </div>
                      <p className="text-xs text-slate-600">
                        File: {ver.file_name} • {(ver.file_size_bytes / 1024).toFixed(1)} KB • Uploaded by{' '}
                        {ver.uploaded_by.full_name} on {new Date(ver.created_at).toLocaleString()}
                      </p>
                      {ver.designer_notes && (
                        <p className="text-xs text-slate-700 italic bg-slate-50 p-1.5 rounded">
                          Designer Note: {ver.designer_notes}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSelectedVersionId(ver.id);
                        setActiveTab('checklist');
                      }}
                      className="text-xs"
                    >
                      Audit v{ver.version_number}
                    </Button>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3 border-b border-slate-100">
              <CardTitle className="text-base font-bold text-slate-900 flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-[#005BBB]" />
                Institutional Review & Decision Audit Trail
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-3">
              {creativeReq.decisions.length === 0 ? (
                <p className="text-xs text-slate-500 italic">No decisions recorded yet.</p>
              ) : (
                creativeReq.decisions.map((dec) => (
                  <div key={dec.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900">{dec.decision}</span>
                      <span className="text-slate-400">{new Date(dec.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-slate-600">
                      Actor: <span className="font-semibold">{dec.actor?.full_name}</span> ({dec.actor_role})
                    </p>
                    {dec.comments && <p className="text-slate-800 bg-white p-2 rounded border border-slate-100 mt-1">&ldquo;{dec.comments}&rdquo;</p>}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* MODAL 1: Assign Designer */}
      {isAssignModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900">Assign Graphic Designer (Step 8)</h3>
              <button onClick={() => setIsAssignModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 uppercase">
                Designer User ID / Email
              </label>
              <input
                type="text"
                placeholder="Enter Designer UUID"
                value={designerIdInput}
                onChange={(e) => setDesignerIdInput(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              />
              <p className="text-xs text-slate-500">
                The user must hold the <span className="font-semibold">CREATIVE_DESIGNER</span> role.
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsAssignModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => assignMutation.mutate(designerIdInput)}
                disabled={!designerIdInput || assignMutation.isPending}
                className="bg-[#001B4D] text-white"
              >
                {assignMutation.isPending ? 'Assigning...' : 'Confirm Assignment'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: Upload Asset Version */}
      {isUploadModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900">Upload Promotional Asset Version</h3>
              <button onClick={() => setIsUploadModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <form onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 uppercase">
                  Asset File (PNG, JPEG, WEBP, PDF &le; 10MB) <span className="text-red-500">*</span>
                </label>
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.webp,.pdf"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-blue-50 file:text-[#005BBB] hover:file:bg-blue-100"
                />
                <p className="text-xs text-slate-500">
                  Binary signatures will be validated. Active markup / SVG is strictly blocked.
                </p>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700 uppercase">
                  Designer Revision Notes
                </label>
                <textarea
                  rows={3}
                  placeholder="Summarize changes or compliance points in this version..."
                  value={designerNotesInput}
                  onChange={(e) => setDesignerNotesInput(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" size="sm" type="button" onClick={() => setIsUploadModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  size="sm"
                  type="submit"
                  disabled={!uploadFile || uploadMutation.isPending}
                  className="bg-[#001B4D] text-white flex items-center gap-1.5"
                >
                  <Upload className="w-4 h-4" />
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload Version'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL 3: Return for Changes */}
      {isCorrectionModalOpen && currentVersion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-slate-900 text-amber-700 flex items-center gap-2">
                <RotateCcw className="w-5 h-5 text-amber-600" />
                Return for Revision (Step 9)
              </h3>
              <button onClick={() => setIsCorrectionModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 uppercase">
                Mandatory Revision Feedback <span className="text-red-500">*</span>
              </label>
              <textarea
                rows={4}
                placeholder="Specify the exact design flaws, QR code issues, or logo adjustments required..."
                value={correctionFeedback}
                onChange={(e) => setCorrectionFeedback(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsCorrectionModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() =>
                  returnCorrectionMutation.mutate({
                    versionId: currentVersion.id,
                    feedback: correctionFeedback,
                  })
                }
                disabled={!correctionFeedback.trim() || returnCorrectionMutation.isPending}
                className="bg-amber-600 hover:bg-amber-700 text-white"
              >
                {returnCorrectionMutation.isPending ? 'Submitting...' : 'Return to Designer'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 4: Placement Head Approval Sign-off */}
      {isApproveModalOpen && currentVersion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-emerald-800 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                Step 9 Creative Sign-Off Gate
              </h3>
              <button onClick={() => setIsApproveModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-xs text-slate-600">
              Formally certifies that <span className="font-semibold">{creativeReq.title}</span> v{currentVersion.version_number} has passed all 4 design verification criteria and is approved for student notification broadcast (Step 10).
            </p>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 uppercase">
                Approval Sign-Off Comments (Optional)
              </label>
              <textarea
                rows={3}
                placeholder="Approved for broadcast on WhatsApp, Portal, and Email channels..."
                value={approveComments}
                onChange={(e) => setApproveComments(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsApproveModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() =>
                  approveMutation.mutate({
                    versionId: currentVersion.id,
                    comments: approveComments,
                  })
                }
                disabled={approveMutation.isPending}
                className="bg-emerald-600 hover:bg-emerald-700 text-white"
              >
                {approveMutation.isPending ? 'Certifying...' : 'Sign Off & Approve'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 5: Reject Asset Version */}
      {isRejectModalOpen && currentVersion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="font-bold text-red-700 flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-red-600" />
                Reject Creative Asset
              </h3>
              <button onClick={() => setIsRejectModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700 uppercase">
                Mandatory Rejection Justification <span className="text-red-500">*</span>
              </label>
              <textarea
                rows={3}
                placeholder="Reason for rejecting this promotional asset..."
                value={rejectionReason}
                onChange={(e) => setRejectionReason(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setIsRejectModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() =>
                  rejectMutation.mutate({
                    versionId: currentVersion.id,
                    reason: rejectionReason,
                  })
                }
                disabled={!rejectionReason.trim() || rejectMutation.isPending}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                {rejectMutation.isPending ? 'Rejecting...' : 'Confirm Rejection'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
