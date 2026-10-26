import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Palette,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  FileText,
  Eye,
  Layers,
  Sparkles,
} from 'lucide-react';
import { creativesApi } from '@/api/creativesApi';
import {
  CreativeRequestListItem,
  CreativeRequestStatus,
  CreativeDeliverableType,
} from '@/types/creatives';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';
import { useAuth } from '@/context/AuthContext';

export const CreativeDirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [deliverableFilter, setDeliverableFilter] = useState<string>('');
  const [priorityFilter, setPriorityFilter] = useState<string>('');
  const [page, setPage] = useState(1);

  const canCreate = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );

  const isDesigner = user?.roles.includes('CREATIVE_DESIGNER');

  const {
    data: creativesData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['creative-requests', { search, statusFilter, deliverableFilter, priorityFilter, page }],
    queryFn: () =>
      creativesApi.getCreativeRequests({
        search: search || undefined,
        status: statusFilter || undefined,
        deliverable_type: deliverableFilter || undefined,
        priority: priorityFilter || undefined,
        page,
      }),
  });

  const { data: metrics } = useQuery({
    queryKey: ['creative-metrics'],
    queryFn: () => creativesApi.getCreativeMetrics(),
  });

  const getStatusBadgeVariant = (status: CreativeRequestStatus): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'REVIEW_PENDING':
        return 'info';
      case 'IN_PRODUCTION':
      case 'ASSIGNED':
        return 'warning';
      case 'CHANGES_REQUESTED':
      case 'REJECTED':
        return 'danger';
      case 'CANCELLED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getDeliverableBadge = (type: CreativeDeliverableType) => {
    switch (type) {
      case 'FLYER':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">Flyer (A4)</span>;
      case 'BANNER':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-purple-100 text-purple-800">Banner</span>;
      case 'SOCIAL_POST':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-pink-100 text-pink-800">Social Post</span>;
      case 'COMBINED_PACK':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">Full Pack</span>;
      default:
        return null;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'URGENT':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">Urgent</span>;
      case 'HIGH':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-amber-100 text-amber-800">High</span>;
      case 'MEDIUM':
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-normal text-slate-600 bg-slate-100">Medium</span>;
      default:
        return <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-normal text-slate-500 bg-slate-100">Low</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Palette className="w-7 h-7 text-[#005BBB]" />
            Creative Studio & Promotional Assets
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Authoritative Workflow Steps 8–9: Produce promotional flyers, display banners, and social posts with 4-point design verification and Placement Head sign-off.
          </p>
        </div>
        <div className="flex items-center gap-3">
          {isDesigner && (
            <Button
              variant="outline"
              onClick={() => navigate('/creatives/my-tasks')}
              className="flex items-center gap-2 border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              <Sparkles className="w-4 h-4 text-purple-600" />
              My Tasks
            </Button>
          )}
          <Button
            variant="outline"
            onClick={() => navigate('/creatives/queue')}
            className="flex items-center gap-2 border-slate-300 text-slate-700 hover:bg-slate-50"
          >
            <Layers className="w-4 h-4 text-[#005BBB]" />
            Review Queues
          </Button>
          {canCreate && (
            <Button
              onClick={() => navigate('/creatives/new')}
              className="flex items-center gap-2 bg-[#001B4D] hover:bg-[#002875] text-white"
            >
              <Plus className="w-4 h-4" />
              New Creative Request
            </Button>
          )}
        </div>
      </div>

      {/* Metric KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-[#001B4D]">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Active Requests</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{metrics?.total_active ?? '-'}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
              <FileText className="w-5 h-5 text-[#001B4D]" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">In Production</p>
              <p className="text-2xl font-bold text-amber-700 mt-1">{metrics?.in_production ?? '-'}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
              <Clock className="w-5 h-5 text-amber-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Review Pending (Step 9)</p>
              <p className="text-2xl font-bold text-blue-700 mt-1">{metrics?.review_pending ?? '-'}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center">
              <Layers className="w-5 h-5 text-blue-600" />
            </div>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-emerald-600">
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Certified for Broadcast</p>
              <p className="text-2xl font-bold text-emerald-700 mt-1">{metrics?.approved ?? '-'}</p>
            </div>
            <div className="w-10 h-10 rounded-full bg-emerald-50 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search requests, briefs, companies..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              />
            </div>

            <div>
              <select
                value={deliverableFilter}
                onChange={(e) => {
                  setDeliverableFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              >
                <option value="">All Deliverable Formats</option>
                <option value="FLYER">Flyer (A4 Document)</option>
                <option value="BANNER">Display Banner</option>
                <option value="SOCIAL_POST">Social Media Post</option>
                <option value="COMBINED_PACK">Combined Creative Pack</option>
              </select>
            </div>

            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              >
                <option value="">All Lifecycle Statuses</option>
                <option value="DRAFT">Draft Brief</option>
                <option value="ASSIGNED">Assigned</option>
                <option value="IN_PRODUCTION">In Production</option>
                <option value="REVIEW_PENDING">Review Pending</option>
                <option value="CHANGES_REQUESTED">Changes Requested</option>
                <option value="APPROVED">Approved (Signed Off)</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <div>
              <select
                value={priorityFilter}
                onChange={(e) => {
                  setPriorityFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#005BBB]"
              >
                <option value="">All Priorities</option>
                <option value="URGENT">Urgent</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Directory Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingState message="Loading creative production requests..." />
          ) : isError ? (
            <ErrorState
              title="Failed to load creative requests"
              message="Could not connect to the Creative Studio service. Please check your credentials and try again."
              onRetry={() => refetch()}
            />
          ) : !creativesData?.data || creativesData.data.length === 0 ? (
            <EmptyState
              title="No Creative Requests Found"
              description="No promotional asset requests match your filters. Create a request from an approved Job Requirement to begin Step 8."
              action={
                canCreate ? (
                  <Button
                    onClick={() => navigate('/creatives/new')}
                    className="bg-[#001B4D] hover:bg-[#002875] text-white"
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Creative Request
                  </Button>
                ) : undefined
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Request / Asset Title</th>
                    <th className="py-3.5 px-4">Approved Job & Company</th>
                    <th className="py-3.5 px-4">Format</th>
                    <th className="py-3.5 px-4">Priority</th>
                    <th className="py-3.5 px-4">Designer</th>
                    <th className="py-3.5 px-4">4-Point Checklist (Step 9)</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {creativesData.data.map((req: CreativeRequestListItem) => {
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
                            <div className="text-xs text-slate-500 font-normal mt-0.5">
                              {req.versions_count > 0 ? (
                                <span className="text-slate-600">Active: v{req.active_version_number}</span>
                              ) : (
                                <span className="text-slate-400 italic">No asset uploaded</span>
                              )}
                            </div>
                          </div>
                        </td>

                        <td className="py-4 px-4">
                          <div className="font-medium text-slate-800">{req.company_name}</div>
                          <div className="text-xs text-slate-500">{req.job_title}</div>
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          {getDeliverableBadge(req.deliverable_type)}
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          {getPriorityBadge(req.priority)}
                        </td>

                        <td className="py-4 px-4">
                          {req.assigned_designer ? (
                            <span className="text-xs font-medium text-slate-800 bg-slate-100 px-2 py-1 rounded">
                              {req.assigned_designer.full_name}
                            </span>
                          ) : (
                            <span className="text-xs text-amber-700 bg-amber-50 px-2 py-0.5 rounded font-medium">
                              Unassigned
                            </span>
                          )}
                        </td>

                        <td className="py-4 px-4">
                          {progress ? (
                            <div className="space-y-1 min-w-[120px]">
                              <div className="flex justify-between text-xs text-slate-600">
                                <span>{progress.verified} of {progress.total} passed</span>
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
                            <span className="text-xs text-slate-400 italic">Awaiting upload</span>
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
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/creatives/${req.id}`);
                            }}
                            className="text-[#005BBB] hover:text-[#001B4D] hover:bg-blue-50"
                          >
                            <Eye className="w-4 h-4 mr-1" />
                            Workspace
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {creativesData?.meta && creativesData.meta.count > 20 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-200">
              <span className="text-xs text-slate-500">
                Showing {creativesData.data.length} of {creativesData.meta.count} creative requests
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={creativesData.data.length < 20}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
