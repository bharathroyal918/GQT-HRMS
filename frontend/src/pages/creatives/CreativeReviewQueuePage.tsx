import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Layers,
  ArrowLeft,
  CheckCircle2,
  FileCheck,
  Eye,
} from 'lucide-react';
import { creativesApi } from '@/api/creativesApi';
import { CreativeRequestListItem } from '@/types/creatives';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

export const CreativeReviewQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [activeQueue, setActiveQueue] = useState<'audit' | 'approval'>('audit');

  // Queue 1: Pending 4-point checklist audits
  const {
    data: reviewQueueData,
    isLoading: isLoadingReview,
    isError: isErrorReview,
    refetch: refetchReview,
  } = useQuery({
    queryKey: ['pending-review-queue'],
    queryFn: () => creativesApi.getPendingReviewQueue(),
  });

  // Queue 2: Awaiting Placement Head sign-off (4/4 verified)
  const allPending = reviewQueueData?.data || [];
  const awaitingHeadSignOff = allPending.filter(
    (req: CreativeRequestListItem) => req.active_version_checklist_progress?.all_verified === true
  );
  const awaitingChecklistAudit = allPending.filter(
    (req: CreativeRequestListItem) => req.active_version_checklist_progress?.all_verified !== true
  );

  const displayList = activeQueue === 'approval' ? awaitingHeadSignOff : awaitingChecklistAudit;
  const isLoading = isLoadingReview;
  const isError = isErrorReview;

  const getStatusBadgeVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'REVIEW_PENDING':
        return 'info';
      case 'IN_PRODUCTION':
        return 'warning';
      case 'CHANGES_REQUESTED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Back button & Header */}
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

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-6 h-6 text-[#005BBB]" />
            Creative Review & Approval Queues (Step 9)
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Dedicated operational review streams for 4-point design verification and Placement Head sign-offs.
          </p>
        </div>
      </div>

      {/* Dual Queue Selector Tabs */}
      <div className="flex border-b border-slate-200 gap-8 text-sm font-semibold">
        <button
          onClick={() => setActiveQueue('audit')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeQueue === 'audit'
              ? 'border-[#005BBB] text-[#001B4D]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FileCheck className="w-4 h-4" />
          Checklist Audits Queue ({awaitingChecklistAudit.length})
        </button>

        <button
          onClick={() => setActiveQueue('approval')}
          className={`pb-3 flex items-center gap-2 border-b-2 transition-colors ${
            activeQueue === 'approval'
              ? 'border-emerald-600 text-emerald-800 font-bold'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          Placement Head Sign-Off Queue ({awaitingHeadSignOff.length})
        </button>
      </div>

      {/* Queue Content Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingState message="Loading review queue..." />
          ) : isError ? (
            <ErrorState
              title="Failed to load review queue"
              message="Could not connect to the Creative Studio service."
              onRetry={() => refetchReview()}
            />
          ) : displayList.length === 0 ? (
            <EmptyState
              title={activeQueue === 'approval' ? 'No Assets Awaiting Head Sign-Off' : 'No Assets Awaiting Checklist Audit'}
              description={
                activeQueue === 'approval'
                  ? 'There are currently no creative assets with 4/4 verified points awaiting final Placement Head sign-off.'
                  : 'All uploaded creative assets have completed their 4-point checklist audits.'
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Request / Asset Title</th>
                    <th className="py-3.5 px-4">Employer & Role</th>
                    <th className="py-3.5 px-4">Deliverable Format</th>
                    <th className="py-3.5 px-4">Designer</th>
                    <th className="py-3.5 px-4">4-Point Progress</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {displayList.map((req: CreativeRequestListItem) => {
                    const progress = req.active_version_checklist_progress;
                    return (
                      <tr
                        key={req.id}
                        onClick={() => navigate(`/creatives/${req.id}`)}
                        className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                      >
                        <td className="py-4 px-4 font-medium text-slate-900">
                          <div>
                            <span className="hover:text-[#005BBB]">{req.title}</span>
                            <div className="text-xs text-slate-500 font-normal">
                              Active: v{req.active_version_number || 1}
                            </div>
                          </div>
                        </td>

                        <td className="py-4 px-4">
                          <div className="font-semibold text-slate-800">{req.company_name}</div>
                          <div className="text-xs text-slate-500">{req.job_title}</div>
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          <span className="text-xs font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                            {req.deliverable_type_display}
                          </span>
                        </td>

                        <td className="py-4 px-4">
                          {req.assigned_designer ? (
                            <span className="text-xs font-medium text-slate-800">
                              {req.assigned_designer.full_name}
                            </span>
                          ) : (
                            <span className="text-xs text-amber-600 font-medium italic">Unassigned</span>
                          )}
                        </td>

                        <td className="py-4 px-4">
                          {progress ? (
                            <div className="space-y-1 min-w-[120px]">
                              <div className="flex justify-between text-xs text-slate-600">
                                <span>{progress.verified}/4 passed</span>
                                <span className="font-semibold">{progress.percent}%</span>
                              </div>
                              <div className="w-full bg-slate-200 rounded-full h-1.5">
                                <div
                                  className={`h-1.5 rounded-full ${
                                    progress.all_verified ? 'bg-emerald-600' : 'bg-[#005BBB]'
                                  }`}
                                  style={{ width: `${progress.percent}%` }}
                                />
                              </div>
                            </div>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No upload</span>
                          )}
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          <StatusBadge
                            variant={getStatusBadgeVariant(req.status)}
                            label={req.status_display}
                          />
                        </td>

                        <td className="py-4 px-4 text-right whitespace-nowrap">
                          <Button
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/creatives/${req.id}`);
                            }}
                            className={
                              activeQueue === 'approval'
                                ? 'bg-emerald-600 hover:bg-emerald-700 text-white text-xs'
                                : 'bg-[#001B4D] hover:bg-[#002875] text-white text-xs'
                            }
                          >
                            <Eye className="w-3.5 h-3.5 mr-1" />
                            {activeQueue === 'approval' ? 'Sign Off Gate' : 'Audit Checklist'}
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
