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
  Mail,
  MessageSquare,
  Bell,
  ShieldAlert,
  Play,
  RefreshCw,
  CheckCheck,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import {
  FollowUpItem,
  CaseEscalation,
  StaffNotification,
  FollowUpReminderItem,
  AutomationRunResult,
  FollowUpCategory,
  ReminderChannel,
} from '../../types/crm';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';
import { AuthContext } from '../../context/AuthContext';

export const FollowUpsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeTab = searchParams.get('tab') || 'overdue';
  const queryClient = useQueryClient();
  const auth = React.useContext(AuthContext);

  const isStaffOrAdmin = auth
    ? auth.hasAnyRole([
        'SUPER_ADMIN',
        'PLACEMENT_DIRECTOR',
        'PLACEMENT_OFFICER',
        'PLACEMENT_COORDINATOR',
      ])
    : true;

  // Modals state
  const [completeModalItem, setCompleteModalItem] = useState<FollowUpItem | null>(null);
  const [completionNotes, setCompletionNotes] = useState('');

  const [rescheduleModalItem, setRescheduleModalItem] = useState<FollowUpItem | null>(null);
  const [newDueDate, setNewDueDate] = useState('');
  const [rescheduleReason, setRescheduleReason] = useState('');

  const [cancelModalItem, setCancelModalItem] = useState<FollowUpItem | null>(null);
  const [cancelReason, setCancelReason] = useState('');

  // Create Follow-up Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCompanyId, setNewCompanyId] = useState('');
  const [newPurpose, setNewPurpose] = useState('');
  const [newPriority, setNewPriority] = useState('MEDIUM');
  const [newDate, setNewDate] = useState('');
  const [newCategory, setNewCategory] = useState<FollowUpCategory>('HR_OUTREACH');
  const [newReminderChannel, setNewReminderChannel] = useState<ReminderChannel>('NONE');
  const [newRemindAt, setNewRemindAt] = useState('');
  const [newNotes, setNewNotes] = useState('');

  // Escalations state
  const [escalationFilter, setEscalationFilter] = useState<string>('ALL');
  const [resolveModalItem, setResolveModalItem] = useState<CaseEscalation | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  // Expanded Reminders State (Follow-up ID -> boolean)
  const [expandedRemindersTaskId, setExpandedRemindersTaskId] = useState<string | null>(null);

  // Automation Run Modal State
  const [showAutomationModal, setShowAutomationModal] = useState(false);
  const [isDryRun, setIsDryRun] = useState(false);
  const [automationResult, setAutomationResult] = useState<AutomationRunResult | null>(null);

  // Fetch companies for creation modal
  const { data: companiesData } = useQuery({
    queryKey: ['companies-dropdown'],
    queryFn: () => crmApi.getCompanies({ page_size: 100 }),
    enabled: showCreateModal,
  });

  // Fetch Unread Notification Count
  const { data: unreadCountData } = useQuery({
    queryKey: ['unread-notifications-count'],
    queryFn: () => crmApi.getUnreadNotificationCount(),
    enabled: activeTab === 'notifications',
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

  const isFollowUpTab = ['overdue', 'today', 'upcoming', 'completed', 'cancelled'].includes(activeTab);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['follow-ups', activeTab],
    queryFn: () => crmApi.getFollowUps(getQueryParams()),
    enabled: isFollowUpTab,
  });

  // Escalations Query
  const {
    data: escalationsData,
    isLoading: isEscalationsLoading,
    error: escalationsError,
    refetch: refetchEscalations,
  } = useQuery({
    queryKey: ['case-escalations', escalationFilter],
    queryFn: () =>
      crmApi.getEscalations(escalationFilter !== 'ALL' ? { status: escalationFilter } : undefined),
    enabled: activeTab === 'escalations',
  });

  // Notifications Query
  const {
    data: notificationsData,
    isLoading: isNotificationsLoading,
    error: notificationsError,
    refetch: refetchNotifications,
  } = useQuery({
    queryKey: ['staff-notifications'],
    queryFn: () => crmApi.getNotifications({ page_size: 50 }),
    enabled: activeTab === 'notifications',
  });

  // Reminders Query for currently expanded follow-up
  const {
    data: activeRemindersData,
    isLoading: isRemindersLoading,
    refetch: refetchReminders,
  } = useQuery({
    queryKey: ['follow-up-reminders', expandedRemindersTaskId],
    queryFn: () => (expandedRemindersTaskId ? crmApi.getFollowUpReminders(expandedRemindersTaskId) : null),
    enabled: Boolean(expandedRemindersTaskId),
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
      setNewCategory('HR_OUTREACH');
      setNewReminderChannel('NONE');
      setNewRemindAt('');
      setNewNotes('');
    },
  });

  // Escalation Mutations
  const acknowledgeEscalationMutation = useMutation({
    mutationFn: (id: string) => crmApi.acknowledgeEscalation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-escalations'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  const resolveEscalationMutation = useMutation({
    mutationFn: ({ id, notes }: { id: string; notes: string }) => crmApi.resolveEscalation(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['case-escalations'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
      setResolveModalItem(null);
      setResolutionNotes('');
    },
  });

  // Notification Mutations
  const markReadMutation = useMutation({
    mutationFn: (id: string) => crmApi.markNotificationRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => crmApi.markAllNotificationsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['staff-notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  // Reminder Retry Mutation
  const retryReminderMutation = useMutation({
    mutationFn: ({ taskId, reminderId }: { taskId: string; reminderId: string }) =>
      crmApi.retryFollowUpReminder(taskId, reminderId),
    onSuccess: () => {
      refetchReminders();
    },
  });

  // Automation Run Mutation
  const runAutomationMutation = useMutation({
    mutationFn: (dryRun: boolean) => crmApi.runAutomationCycle(dryRun),
    onSuccess: (res) => {
      setAutomationResult(res);
      queryClient.invalidateQueries({ queryKey: ['follow-ups'] });
      queryClient.invalidateQueries({ queryKey: ['case-escalations'] });
      queryClient.invalidateQueries({ queryKey: ['staff-notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCompanyId || !newPurpose || !newDate) return;
    const payload: Record<string, unknown> = {
      company: newCompanyId,
      purpose: newPurpose,
      priority: newPriority,
      category: newCategory,
      reminder_channel: newReminderChannel,
      due_date: new Date(newDate).toISOString(),
    };
    if (newRemindAt) {
      payload.remind_at = new Date(newRemindAt).toISOString();
    }
    if (newNotes.trim()) {
      payload.notes = newNotes.trim();
    }
    createMutation.mutate(payload);
  };

  const unreadCount = unreadCountData?.count ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Corporate Follow-Up Workspace</h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Automated corporate nurturing, multi-channel reminders, officer alerts, and SLA escalations (Phase 12).
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          {isStaffOrAdmin && (
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Play className="w-3.5 h-3.5 text-gqt-blue" />}
              onClick={() => {
                setShowAutomationModal(true);
                setAutomationResult(null);
              }}
            >
              Automation Cycle
            </Button>
          )}
          <Button
            variant="primary"
            size="sm"
            leftIcon={<Plus className="w-4 h-4" />}
            onClick={() => setShowCreateModal(true)}
          >
            Schedule Follow-up
          </Button>
        </div>
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
          <button
            onClick={() => setSearchParams({ tab: 'escalations' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'escalations'
                ? 'border-amber-600 text-amber-700 font-extrabold'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <ShieldAlert className="w-4 h-4" /> Escalations
          </button>
          <button
            onClick={() => setSearchParams({ tab: 'notifications' })}
            className={`py-3 flex items-center gap-2 border-b-2 whitespace-nowrap transition-colors ${
              activeTab === 'notifications'
                ? 'border-gqt-blue text-gqt-blue font-extrabold'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Bell className="w-4 h-4" /> Officer Alerts
            {unreadCount > 0 && (
              <span className="px-1.5 py-0.2 bg-red-600 text-white rounded-full text-[10px] font-bold">
                {unreadCount}
              </span>
            )}
          </button>
        </nav>
      </div>

      {/* TAB CONTENT: ESCALATIONS */}
      {activeTab === 'escalations' && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-3 bg-amber-50/50 p-3 rounded-lg border border-amber-200">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-600" />
              <span className="text-xs font-bold text-amber-900">
                SLA & Overdue Case Escalations
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gqt-neutral-600 font-medium">Status Filter:</span>
              <select
                value={escalationFilter}
                onChange={(e) => setEscalationFilter(e.target.value)}
                className="px-2.5 py-1 text-xs border border-gqt-neutral-300 rounded-md bg-white focus:ring-1 focus:ring-gqt-blue"
              >
                <option value="ALL">All Statuses</option>
                <option value="PENDING">Pending Attention</option>
                <option value="ACKNOWLEDGED">Acknowledged</option>
                <option value="RESOLVED">Resolved</option>
                <option value="DISMISSED">Dismissed</option>
              </select>
            </div>
          </div>

          {isEscalationsLoading ? (
            <LoadingState message="Loading case escalations..." />
          ) : escalationsError ? (
            <ErrorState
              title="Could not load escalations"
              message={escalationsError instanceof Error ? escalationsError.message : 'Network error'}
              onRetry={() => refetchEscalations()}
            />
          ) : !escalationsData || escalationsData.data.length === 0 ? (
            <EmptyState
              title="No Escalation Cases Found"
              description="No cases match the selected filter. Overdue follow-ups past SLA threshold will appear here."
            />
          ) : (
            <div className="space-y-3.5">
              {escalationsData.data.map((esc) => (
                <Card
                  key={esc.id}
                  className={`p-4 border-l-4 ${
                    esc.status === 'PENDING'
                      ? 'border-l-red-500 bg-red-50/15'
                      : esc.status === 'ACKNOWLEDGED'
                      ? 'border-l-amber-500 bg-amber-50/10'
                      : 'border-l-emerald-500'
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                    <div className="space-y-1.5 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            esc.status === 'PENDING'
                              ? 'bg-red-100 text-red-700'
                              : esc.status === 'ACKNOWLEDGED'
                              ? 'bg-amber-100 text-amber-700'
                              : 'bg-emerald-100 text-emerald-700'
                          }`}
                        >
                          {esc.status}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-navy">
                          {esc.escalation_level}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-amber-100 text-amber-800">
                          {esc.case_type.replace('_', ' ')}
                        </span>
                        <span className="text-[11px] text-gqt-neutral-500">
                          Triggered: {new Date(esc.created_at).toLocaleString()}
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-gqt-navy">{esc.reason}</h4>

                      {esc.follow_up_purpose && (
                        <div className="text-xs text-gqt-neutral-600 bg-gqt-neutral-50 p-2 rounded border border-gqt-neutral-200">
                          <strong>Target Follow-up:</strong> {esc.follow_up_purpose} (Company:{' '}
                          {esc.company_name}) {esc.follow_up_due_date ? `• Due: ${new Date(esc.follow_up_due_date).toLocaleString()}` : ''}
                        </div>
                      )}

                      <div className="flex flex-wrap items-center gap-3 text-xs text-gqt-neutral-600">
                        {esc.escalated_to_name && (
                          <span>
                            Supervisor: <strong>{esc.escalated_to_name || esc.escalated_to_email}</strong>
                          </span>
                        )}
                        {esc.acknowledged_at && (
                          <span className="text-amber-700 font-medium">
                            Acknowledged on {new Date(esc.acknowledged_at).toLocaleString()}
                          </span>
                        )}
                        {esc.resolved_at && (
                          <span className="text-emerald-700 font-medium">
                            Resolved on {new Date(esc.resolved_at).toLocaleString()}
                          </span>
                        )}
                      </div>

                      {esc.resolution_notes && (
                        <div className="text-xs bg-emerald-50 text-emerald-900 p-2.5 rounded border border-emerald-200">
                          <strong>Resolution Notes:</strong> {esc.resolution_notes}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    {esc.status !== 'RESOLVED' && esc.status !== 'DISMISSED' && (
                      <div className="flex sm:flex-col gap-2 flex-shrink-0">
                        {esc.status === 'PENDING' && (
                          <Button
                            size="sm"
                            variant="outline"
                            isLoading={acknowledgeEscalationMutation.isPending}
                            onClick={() => acknowledgeEscalationMutation.mutate(esc.id)}
                          >
                            Acknowledge
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => setResolveModalItem(esc)}
                        >
                          Resolve Case
                        </Button>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: NOTIFICATIONS */}
      {activeTab === 'notifications' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between gap-4 bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200">
            <div className="flex items-center gap-2">
              <Bell className="w-5 h-5 text-gqt-blue" />
              <span className="text-xs font-bold text-gqt-navy">
                Placement Officer Automated Notifications ({unreadCount} unread)
              </span>
            </div>
            {unreadCount > 0 && (
              <Button
                variant="outline"
                size="sm"
                leftIcon={<CheckCheck className="w-3.5 h-3.5" />}
                isLoading={markAllReadMutation.isPending}
                onClick={() => markAllReadMutation.mutate()}
              >
                Mark All Read
              </Button>
            )}
          </div>

          {isNotificationsLoading ? (
            <LoadingState message="Loading notifications..." />
          ) : notificationsError ? (
            <ErrorState
              title="Could not load notifications"
              message={notificationsError instanceof Error ? notificationsError.message : 'Network error'}
              onRetry={() => refetchNotifications()}
            />
          ) : !notificationsData || notificationsData.data.length === 0 ? (
            <EmptyState
              title="No Notifications"
              description="You have no notifications in your activity feed at this time."
            />
          ) : (
            <div className="space-y-2.5">
              {notificationsData.data.map((notif: StaffNotification) => (
                <Card
                  key={notif.id}
                  className={`p-3.5 transition-colors border-l-4 ${
                    !notif.is_read
                      ? 'border-l-gqt-blue bg-blue-50/20'
                      : 'border-l-gqt-neutral-300 opacity-80'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-navy">
                          {notif.notification_type.replace('_', ' ')}
                        </span>
                        <span className="text-[11px] text-gqt-neutral-500">
                          {new Date(notif.created_at).toLocaleString()}
                        </span>
                        {!notif.is_read && (
                          <span className="w-2 h-2 rounded-full bg-gqt-blue animate-pulse" />
                        )}
                      </div>
                      <h4 className="text-xs font-bold text-gqt-navy">{notif.title}</h4>
                      <p className="text-xs text-gqt-neutral-600">{notif.message}</p>
                    </div>

                    {!notif.is_read && (
                      <Button
                        size="sm"
                        variant="ghost"
                        className="text-xs text-gqt-blue hover:bg-blue-50"
                        isLoading={markReadMutation.isPending}
                        onClick={() => markReadMutation.mutate(notif.id)}
                      >
                        Mark Read
                      </Button>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: FOLLOW-UPS LIST */}
      {isFollowUpTab && (
        <>
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
                        {task.category && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-blue-50 text-gqt-blue border border-blue-200">
                            {task.category.replace('_', ' ')}
                          </span>
                        )}
                        {task.reminder_channel && task.reminder_channel !== 'NONE' && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-50 text-purple-700 border border-purple-200 flex items-center gap-1">
                            {task.reminder_channel === 'EMAIL' && <Mail className="w-3 h-3" />}
                            {task.reminder_channel === 'WHATSAPP' && <MessageSquare className="w-3 h-3" />}
                            {task.reminder_channel === 'BOTH' && (
                              <>
                                <Mail className="w-3 h-3" />
                                <MessageSquare className="w-3 h-3" />
                              </>
                            )}
                            {task.reminder_channel} REMINDER
                          </span>
                        )}
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
                        Target Due:{' '}
                        <strong className={task.is_overdue ? 'text-red-600' : 'text-gqt-navy'}>
                          {new Date(task.due_date).toLocaleString()}
                        </strong>{' '}
                        • Assigned to: <strong>{task.assigned_to.full_name || task.assigned_to.email}</strong>
                        {task.remind_at && (
                          <>
                            {' '}
                            • Remind At:{' '}
                            <strong className="text-purple-700">
                              {new Date(task.remind_at).toLocaleString()}
                            </strong>
                          </>
                        )}
                      </p>

                      {task.notes && (
                        <div className="mt-2 text-xs bg-gqt-neutral-50 text-gqt-neutral-700 p-2.5 rounded-lg border border-gqt-neutral-200">
                          <strong>Notes:</strong> {task.notes}
                        </div>
                      )}

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

                      {/* Reminder Outbox Toggle */}
                      {task.reminder_channel && task.reminder_channel !== 'NONE' && (
                        <div className="pt-2">
                          <button
                            type="button"
                            onClick={() =>
                              setExpandedRemindersTaskId(
                                expandedRemindersTaskId === task.id ? null : task.id
                              )
                            }
                            className="text-[11px] font-bold text-gqt-blue hover:underline flex items-center gap-1"
                          >
                            {expandedRemindersTaskId === task.id ? (
                              <>
                                <ChevronUp className="w-3.5 h-3.5" /> Hide Automated Reminder Outbox
                              </>
                            ) : (
                              <>
                                <ChevronDown className="w-3.5 h-3.5" /> View Automated Reminder Outbox
                              </>
                            )}
                          </button>

                          {expandedRemindersTaskId === task.id && (
                            <div className="mt-2 p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-200 space-y-2">
                              <h5 className="text-[11px] font-bold text-gqt-navy uppercase">
                                Outbox Delivery Queue
                              </h5>
                              {isRemindersLoading ? (
                                <p className="text-xs text-gqt-neutral-500">Loading outbox...</p>
                              ) : !activeRemindersData?.data || activeRemindersData.data.length === 0 ? (
                                <p className="text-xs text-gqt-neutral-500">
                                  No automated reminder items currently queued for this task.
                                </p>
                              ) : (
                                <div className="space-y-1.5">
                                  {activeRemindersData.data.map((item: FollowUpReminderItem) => (
                                    <div
                                      key={item.id}
                                      className="flex flex-wrap items-center justify-between text-xs p-2 bg-white rounded border border-gqt-neutral-200 gap-2"
                                    >
                                      <div className="space-y-0.5">
                                        <div className="flex items-center gap-2">
                                          <span className="font-bold text-gqt-navy">
                                            {item.channel}
                                          </span>
                                          <span
                                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold uppercase ${
                                              item.is_simulated
                                                ? 'bg-purple-100 text-purple-800'
                                                : item.status === 'SENT' || item.status === 'DELIVERED'
                                                ? 'bg-emerald-100 text-emerald-800'
                                                : item.status === 'FAILED'
                                                ? 'bg-red-100 text-red-800'
                                                : 'bg-amber-100 text-amber-800'
                                            }`}
                                          >
                                            {item.is_simulated ? 'SIMULATED' : item.status}
                                          </span>
                                          <span className="text-[10px] text-gqt-neutral-500">
                                            To: {item.recipient}
                                          </span>
                                        </div>
                                        {item.error_message && (
                                          <p className="text-[11px] text-red-600">
                                            Error: {item.error_message}
                                          </p>
                                        )}
                                      </div>
                                      {item.status === 'FAILED' && (
                                        <Button
                                          size="sm"
                                          variant="outline"
                                          leftIcon={<RefreshCw className="w-3 h-3" />}
                                          isLoading={retryReminderMutation.isPending}
                                          onClick={() =>
                                            retryReminderMutation.mutate({
                                              taskId: task.id,
                                              reminderId: item.id,
                                            })
                                          }
                                        >
                                          Retry
                                        </Button>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          )}
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
        </>
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

      {/* Resolve Escalation Modal */}
      {resolveModalItem && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              Resolve Case Escalation
            </h3>
            <p className="text-xs text-gqt-neutral-600">
              Resolving escalation: <strong>{resolveModalItem.reason}</strong>
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-gqt-navy uppercase">Resolution Notes *</label>
              <textarea
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                rows={3}
                placeholder="Document resolution outcome (e.g. Contacted HR directly, rescheduled drive date)..."
                className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                required
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button size="sm" variant="outline" onClick={() => setResolveModalItem(null)}>
                Cancel
              </Button>
              <Button
                size="sm"
                variant="primary"
                disabled={!resolutionNotes.trim()}
                isLoading={resolveEscalationMutation.isPending}
                onClick={() =>
                  resolveEscalationMutation.mutate({
                    id: resolveModalItem.id,
                    notes: resolutionNotes.trim(),
                  })
                }
              >
                Confirm Resolution
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Schedule Follow-up Creation Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
          <Card className="max-w-lg w-full p-6 space-y-4 my-8">
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
                  <label className="text-xs font-bold text-gqt-navy uppercase">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value as FollowUpCategory)}
                    className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
                  >
                    <option value="HR_OUTREACH">HR Outreach</option>
                    <option value="STUDENT_RECONNECT">Student Reconnect</option>
                    <option value="INTERVIEW_CONFIRMATION">Interview Confirmation</option>
                    <option value="OFFER_ACCEPTANCE">Offer Acceptance</option>
                    <option value="JOINING_CHECK">Joining Check</option>
                    <option value="GENERAL_RECONNECT">General Reconnect</option>
                  </select>
                </div>

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
              </div>

              <div className="grid grid-cols-2 gap-3">
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

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gqt-navy uppercase">Reminder Channel</label>
                  <select
                    value={newReminderChannel}
                    onChange={(e) => setNewReminderChannel(e.target.value as ReminderChannel)}
                    className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue bg-white"
                  >
                    <option value="NONE">No Automated Reminder</option>
                    <option value="EMAIL">Email Reminder</option>
                    <option value="WHATSAPP">WhatsApp Reminder</option>
                    <option value="BOTH">Email & WhatsApp</option>
                  </select>
                </div>
              </div>

              {newReminderChannel !== 'NONE' && (
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-gqt-navy uppercase">
                    Remind At (Leave blank to remind at Due Time)
                  </label>
                  <input
                    type="datetime-local"
                    value={newRemindAt}
                    onChange={(e) => setNewRemindAt(e.target.value)}
                    className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  />
                </div>
              )}

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gqt-navy uppercase">Notes / Instructions</label>
                <textarea
                  value={newNotes}
                  onChange={(e) => setNewNotes(e.target.value)}
                  rows={2}
                  placeholder="Additional context or talking points..."
                  className="w-full px-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                />
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

      {/* Automation Trigger Modal */}
      {showAutomationModal && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <Card className="max-w-md w-full p-6 space-y-4">
            <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
              <Play className="w-5 h-5 text-gqt-blue" />
              Run Automation Follow-up Cycle
            </h3>
            <p className="text-xs text-gqt-neutral-600">
              Triggers the background engine to process due reminder outbox items, generate placement officer alerts, and evaluate overdue SLA escalations.
            </p>

            <div className="flex items-center gap-2 p-3 bg-gqt-neutral-50 rounded-lg border border-gqt-neutral-200">
              <input
                type="checkbox"
                id="dryRunCheck"
                checked={isDryRun}
                onChange={(e) => setIsDryRun(e.target.checked)}
                className="w-4 h-4 text-gqt-blue rounded border-gqt-neutral-300 focus:ring-gqt-blue"
              />
              <label htmlFor="dryRunCheck" className="text-xs font-semibold text-gqt-navy cursor-pointer">
                Dry Run Mode (Simulate detection without modifying states or sending)
              </label>
            </div>

            {automationResult && (
              <div className="p-3 bg-blue-50/50 rounded-lg border border-blue-200 text-xs space-y-1">
                <p className="font-bold text-gqt-navy">Execution Result:</p>
                <p className="text-gqt-neutral-700">Mode: <strong>{automationResult.dry_run ? 'Dry Run' : 'Live Execution'}</strong></p>
                <p className="text-gqt-neutral-700">Reminders: <strong>{automationResult.reminders_processed ?? automationResult.reminders_eligible ?? 0}</strong></p>
                <p className="text-gqt-neutral-700">Officer Notifications: <strong>{automationResult.notifications_created ?? automationResult.due_notifications_eligible ?? 0}</strong></p>
                <p className="text-gqt-neutral-700">Escalations: <strong>{automationResult.escalations_created ?? automationResult.overdue_escalations_eligible ?? 0}</strong></p>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-gqt-neutral-100">
              <Button size="sm" variant="outline" onClick={() => setShowAutomationModal(false)}>
                Close
              </Button>
              <Button
                size="sm"
                variant="primary"
                isLoading={runAutomationMutation.isPending}
                onClick={() => runAutomationMutation.mutate(isDryRun)}
              >
                Execute Cycle
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};
