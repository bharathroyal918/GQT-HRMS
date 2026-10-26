import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowLeft,
  Clock,
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

export const DesignerWorkQueuePage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: queueData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['designer-queue'],
    queryFn: () => creativesApi.getDesignerQueue(),
  });

  const getStatusBadgeVariant = (status: string): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'REVIEW_PENDING':
        return 'info';
      case 'IN_PRODUCTION':
      case 'ASSIGNED':
        return 'warning';
      case 'CHANGES_REQUESTED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
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

      <div>
        <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-purple-600" />
          Designer Workbench — My Assigned Tasks
        </h1>
        <p className="text-sm text-slate-600 mt-1">
          Promotional creative requests assigned to you for drafting, revisions, and Step 9 compliance audits.
        </p>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <LoadingState message="Loading your assigned tasks..." />
          ) : isError ? (
            <ErrorState
              title="Failed to load designer queue"
              message="Could not connect to the Creative Studio service."
              onRetry={() => refetch()}
            />
          ) : !queueData?.data || queueData.data.length === 0 ? (
            <EmptyState
              title="No Tasks Assigned"
              description="You currently have no active creative requests assigned to your queue."
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-600 uppercase tracking-wider">
                  <tr>
                    <th className="py-3.5 px-4">Campaign Title</th>
                    <th className="py-3.5 px-4">Approved Job</th>
                    <th className="py-3.5 px-4">Format</th>
                    <th className="py-3.5 px-4">Priority</th>
                    <th className="py-3.5 px-4">Production Deadline</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {queueData.data.map((req: CreativeRequestListItem) => {
                    const isUrgent = req.priority === 'URGENT';
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
                              Active Version: v{req.active_version_number || 1}
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

                        <td className="py-4 px-4 whitespace-nowrap">
                          {isUrgent ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">
                              Urgent
                            </span>
                          ) : (
                            <span className="text-xs font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">
                              {req.priority}
                            </span>
                          )}
                        </td>

                        <td className="py-4 px-4 whitespace-nowrap">
                          {req.production_deadline ? (
                            <span className="text-xs text-slate-700 flex items-center gap-1">
                              <Clock className="w-3.5 h-3.5 text-slate-400" />
                              {new Date(req.production_deadline).toLocaleDateString()}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400 italic">No deadline set</span>
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
                            className="bg-[#001B4D] hover:bg-[#002875] text-white text-xs"
                          >
                            <Eye className="w-3.5 h-3.5 mr-1" />
                            Open Workspace
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
