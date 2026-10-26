import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Calendar,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Plus,
  RotateCcw,
  Building2,
  Users,
  Check,
} from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { FollowUpItem } from '../../types/crm';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';

export const FollowUpsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overdue';
  const queryClient = useQueryClient();

  // Modals state
  const [completeModalItem, setCompleteModalItem] = useState<FollowUpItem | null>(null);
  const [completionNotes, setCompletionNotes] = useState('');

  const [rescheduleModalItem, setRescheduleModalItem] = useState<FollowUpItem | null>(null);
  const [newDueDate, setNewDueDate] = useState('');
  const [rescheduleReason, setRescheduleReason] = useState('');

  const [cancelModalItem, setCancelModalItem] = useState<FollowUpItem | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCompanyId, setNewCompanyId] = useState('');
  const [newPurpose, setNewPurpose] = useState('');
  const [newPriority, setNewPriority] = useState('MEDIUM');
  const [newDate, setNewDate] = useState('');

  // Fetch companies for creation modal
  const { data: companiesData } = useQuery({
    queryKey: ['companies-dropdown'],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
    enabled: showCreateModal,
  });

  // Query parameters according to active tab
  const getQueryParams = () => {
    if (activeTab === 'overdue') {
      return { is_overdue: true };
    }
    if (activeTab === 'today') {
      const todayStr = new Date().toISOString().split('T')[0];
      return { status: 'OPEN', due_date_from: `${todayStr}T00:00:00Z`, due_date_to: `${todayStr}T23:59:59Z` };
    }
    if (activeTab === 'upcoming') {
      return { status: 'OPEN', is_overdue: false };
    }
    if (activeTab === 'completed') {
      return { status: 'COMPLETED' };
    }
    if (activeTab === 'cancelled') {
      return { status: 'CANCELLED' };
    }
    return {};
  };

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['follow-ups', activeTab],
    queryFn: () => crmApi.getFollowUps(getQueryParams()),
  });

  // Mutations
  const completeMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => crmApi.completeFollowUp(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      setCompleteModalItem(null);
      setCompletionNotes('');
    },
  });

  const rescheduleMutation = useMutation({
    mutationFn: ({ id, date, reason }: { id: string; date: string; reason: string }) =>
      crmApi.rescheduleFollowUp(id, date, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      setRescheduleModalItem(null);
      setNewDueDate('');
      setRescheduleReason('');
    },
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => crmApi.cancelFollowUp(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      setCancelModalItem(null);
      setCancelReason('');
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => crmApi.createFollowUp(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      queryClient.invalidateQueries({ queryKey: ['crm-dashboard-metrics'] });
      setShowCreateModal(false);
      setNewPurpose('');
      setNewCompanyId('');
      setNewDate('');
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompanyId || !newPurpose || !newDate) return;
    createMutation.mutate({
      company: newCompanyId,
      purpose: newPurpose,
      priority: newPriority,
      due_date: new Date(newDate).toISOString(),
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Corporate Follow-Up Workspace</h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Scheduled corporate nurturing callbacks and relationship commitments (Workflow Step 4).
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          leftIcon={<Plus className="w-4 h-4" />}
          onClick={() => setShowCreateModal(true)}
        >
          Schedule Follow-up
        </Button>
      </div>

      {/* Workspace Navigation Tabs */}
      <div className="border-b border-gqt-neutral-200">
        <nav className="flex gap-4 sm:gap-6 -mb-px text-xs font-bold uppercase tracking-wider overflow-x-auto">
          <button
            onClick={() => setSearchParams({ tab: 'overdue' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'overdue'
                ? 'border-red-600 text-red-600'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <AlertTriangle className="w-4 h-4" /> Overdue Tasks
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'today' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'today'
                ? 'border-amber-600 text-amber-600'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Clock className="w-4 h-4" /> Due Today
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'upcoming' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'upcoming'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Calendar className="w-4 h-4" /> Upcoming Open
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'completed' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'completed'
                ? 'border-emerald-600 text-emerald-600'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" /> Completed
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'cancelled' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'cancelled'
                ? 'border-gqt-neutral-600 text-gqt-neutral-600'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <XCircle className="w-4 h-4" /> Cancelled
          </button>
        </nav>
      </div>

      {/* Task List */}
      {isLoading ? (
        <LoadingState message="Loading follow-up tasks..." />
      ) : error ? (
        <ErrorState
          title="Could not load follow-ups"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      ) : !data || data.data.length === 0 ? (
        <EmptyState
          title={`No ${activeTab.toUpperCase()} Follow-ups`}
          description={
            activeTab === 'overdue'
              ? 'Great job! There are no overdue corporate follow-ups in the queue.'
              : 'No follow-up tasks registered under this view.'
          }
          action={
            <Button size="sm" variant="primary" onClick={() => setShowCreateModal(true)}>
              Schedule New Task
            </Button>
          }
        />
      ) : (
        <div className="space-y-3.5">
          {data.data.map((task) => (
            <Card
              key={task.id}
              className={`p-4 transition-all border-l-4 ${
                task.is_overdue
                  ? 'border-l-red-500 bg-red-50/20'
                  : task.status === 'COMPLETED'
                  ? 'border-l-emerald-500'
                  : task.priority === 'URGENT'
                  ? 'border-l-amber-500'
                  : 'border-l-gqt-blue'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        task.is_overdue
                          ? 'bg-red-100 text-red-700'
                          : task.status === 'COMPLETED'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-gqt-neutral-100 text-gqt-neutral-700'
                      }`}
                    >
                      {task.is_overdue ? 'OVERDUE' : task.status}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        task.priority === 'URGENT'
                          ? 'bg-red-50 text-red-600 border border-red-200'
                          : task.priority === 'HIGH'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-gqt-neutral-50 text-gqt-neutral-600'
                      }`}
                    >
                      {task.priority} Priority
                    </span>
                    {task.rescheduled_count > 0 && (
                      <span className="text-[10px] text-gqt-neutral-500 font-semibold flex items-center gap-1">
                        <RotateCcw className="w-3 h-3 text-gqt-blue" /> Rescheduled {task.rescheduled_count}x
                      </span>
                    )}
                  </div>

                  <h3 className="text-sm font-bold text-gqt-navy">{task.purpose}</h3>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-gqt-charcoal">
                    <Link
                      to={`/crm/companies/${task.company.id}`}
                      className="font-bold text-gqt-navy hover:text-gqt-blue flex items-center gap-1"
                    >
                      <Building2 className="w-3.5 h-3.5 text-gqt-blue" />
                      {task.company.name}
                    </Link>
                    {task.hr_contact && (
                      <span className="flex items-center gap-1 font-medium">
                        <Users className="w-3.5 h-3.5 text-emerald-600" />
                        {task.hr_contact.name} ({task.hr_contact.phone || task.hr_contact.email})
                      </span>
                    )}
                  </div>

                  <p className="text-[11px] text-gqt-neutral-500">
                    Target Due: <strong className={task.is_overdue ? 'text-red-600' : 'text-gqt-navy'}>{new Date(task.due_date).toLocaleString()}</strong> •
                    Assigned to: <strong>{task.assigned_to.full_name || task.assigned_to.email}</strong>
                  </p>

                  {task.completion_notes && (
                    <div className="mt-2 text-xs bg-emerald-50 text-emerald-900 p-2.5 rounded-lg border border-emerald-200">
                      <strong>Completion Notes:</strong> {task.completion_notes}
                    </div>
                  )}

                  {task.cancellation_reason && (
                    <div className="mt-2 text-xs bg-gqt-neutral-50 text-gqt-neutral-700 p-2.5 rounded-lg border border-gqt-neutral-200">
                      <strong>Cancellation Reason:</strong> {task.cancellation_reason}
                    </div>
                  )}
                </div>

                {/* Actions */}
                {task.status !== 'COMPLETED' && task.status !== 'CANCELLED' && (
                  <div className="flex sm:flex-col gap-2 flex-shrink-0">
                    <Button
                      size="sm"
                      variant="primary"
                      leftIcon={<Check className="w-3.5 h-3.5" />}
                      onClick={() => setCompleteModalItem(task)}
                    >
                      Complete
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
                      onClick={() => setRescheduleModalItem(task)}
                    >
                      Reschedule
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-red-600 hover:bg-red-50"
                      onClick={() => setCancelModalItem(task)}
                    >
                      Cancel
                    </Button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Complete Task Modal */}
      {completeModalItem && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Complete Follow-Up Task
            </h3>
            <p className="text-xs text-gqt-neutral-600">
              Mark follow-up for <strong>{completeModalItem.company.name}</strong> as completed.
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase">Completion Notes (Optional)</label>
              <textarea
                value={completionNotes}
                onChange={(e) => setCompletionNotes(e.target.value)}
                rows={3}
                placeholder="What was the result of this follow-up? (e.g. Received JD, agreed on drive date...)"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => setCompleteModalItem(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="primary"
                isLoading={completeMutation.isPending}
                onClick={() => completeMutation.mutate({ id: completeModalItem.id, notes: completionNotes })}
              >
                Confirm Completion
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Reschedule Task Modal */}
      {rescheduleModalItem && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
              <RotateCcw className="w-5 h-5 text-gqt-blue" />
              Reschedule Follow-Up Task
            </h3>
            <p className="text-xs text-gqt-neutral-600">
              Move follow-up for <strong>{rescheduleModalItem.company.name}</strong> to a new date and time.
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase">New Due Date & Time *</label>
              <input
                type="datetime-local"
                value={newDueDate}
                onChange={(e) => setNewDueDate(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase">Reason for Rescheduling</label>
              <input
                type="text"
                value={rescheduleReason}
                onChange={(e) => setRescheduleReason(e.target.value)}
                placeholder="e.g. HR requested call next Wednesday"
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => setRescheduleModalItem(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="primary"
                disabled={!newDueDate}
                isLoading={rescheduleMutation.isPending}
                onClick={() =>
                  rescheduleMutation.mutate({
                    id: rescheduleModalItem.id,
                    date: new Date(newDueDate).toISOString(),
                    reason: rescheduleReason,
                  })
                }
              >
                Confirm Reschedule
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Cancel Task Modal */}
      {cancelModalItem && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-red-600 flex items-center gap-2">
              <XCircle className="w-5 h-5 text-red-600" />
              Cancel Follow-Up Task
            </h3>
            <p className="text-xs text-gqt-neutral-600">
              Are you sure you want to cancel the task for <strong>{cancelModalItem.company.name}</strong>?
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase">Cancellation Reason *</label>
              <textarea
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                rows={2}
                placeholder="Explicit business reason (e.g. HR confirmed no fresher hiring this year)..."
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => setCancelModalItem(null)}>
                Dismiss
              </Button>
              <Button
                size="sm"
                variant="danger"
                disabled={!cancelReason.trim()}
                isLoading={cancelMutation.isPending}
                onClick={() => cancelMutation.mutate({ id: cancelModalItem.id, reason: cancelReason })}
              >
                Confirm Cancellation
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Schedule Follow-up Creation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
              <Calendar className="w-5 h-5 text-gqt-blue" />
              Schedule Follow-Up Task
            </h3>
            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gqt-navy uppercase">Target Corporate Company *</label>
                <select
                  value={newCompanyId}
                  onChange={(e) => setNewCompanyId(e.target.value)}
                  className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
                  required
                >
                  <option value="">Select Company...</option>
                  {companiesData?.data.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gqt-navy uppercase">Purpose / Objective *</label>
                <input
                  type="text"
                  value={newPurpose}
                  onChange={(e) => setNewPurpose(e.target.value)}
                  placeholder="e.g. Follow up on 2026 Batch placement brochure"
                  className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gqt-navy uppercase">Priority</label>
                  <select
                    value={newPriority}
                    onChange={(e) => setNewPriority(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
                  >
                    <option value="LOW">Low</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="HIGH">High</option>
                    <option value="URGENT">Urgent</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gqt-navy uppercase">Due Date & Time *</label>
                  <input
                    type="datetime-local"
                    value={newDate}
                    onChange={(e) => setNewDate(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-gqt-neutral-100">
                <Button size="sm" variant="outline" type="button" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button size="sm" variant="primary" type="submit" isLoading={createMutation.isPending}>
                  Schedule Task
                </Button>
              </div>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
};
