import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCheck,
  Briefcase,
  Send,
  Calendar,
  Award,
  PhoneCall,
  Info,
  ChevronLeft,
  ChevronRight,
  Filter,
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { notificationsApi } from '@/api/notificationsApi';
import { NotificationCategory, NotificationItem } from '@/types/notifications';

const getCategoryIcon = (category: NotificationCategory) => {
  switch (category) {
    case 'JOB_DRIVE':
      return <Briefcase className="w-5 h-5 text-gqt-blue" />;
    case 'APPLICATION':
      return <Send className="w-5 h-5 text-emerald-600" />;
    case 'INTERVIEW':
      return <Calendar className="w-5 h-5 text-indigo-600" />;
    case 'PLACEMENT':
      return <Award className="w-5 h-5 text-amber-600" />;
    case 'FOLLOW_UP':
      return <PhoneCall className="w-5 h-5 text-purple-600" />;
    case 'SYSTEM':
    default:
      return <Info className="w-5 h-5 text-gqt-neutral-500" />;
  }
};

const getCategoryBadgeClass = (category: NotificationCategory) => {
  switch (category) {
    case 'JOB_DRIVE':
      return 'bg-blue-50 text-gqt-blue border-blue-200';
    case 'APPLICATION':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'INTERVIEW':
      return 'bg-indigo-50 text-indigo-700 border-indigo-200';
    case 'PLACEMENT':
      return 'bg-amber-50 text-amber-700 border-amber-200';
    case 'FOLLOW_UP':
      return 'bg-purple-50 text-purple-700 border-purple-200';
    case 'SYSTEM':
    default:
      return 'bg-gqt-neutral-100 text-gqt-neutral-700 border-gqt-neutral-300';
  }
};

export const NotificationsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState<'all' | 'unread' | 'JOB_DRIVE' | 'APPLICATION' | 'FOLLOW_UP'>('all');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const pageSize = 15;

  const filters = {
    page: currentPage,
    page_size: pageSize,
    ...(activeTab === 'unread' ? { is_read: false } : {}),
    ...(activeTab !== 'all' && activeTab !== 'unread' ? { category: activeTab } : {}),
  };

  const {
    data: notificationsResponse,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['notifications', 'page', filters],
    queryFn: () => notificationsApi.listNotifications(filters),
  });

  const { data: countData } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsApi.getUnreadCount(),
  });

  const unreadCount = countData?.count ?? 0;

  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  const notifications = notificationsResponse?.data || [];
  const meta = notificationsResponse?.meta;
  const totalPages = meta?.total_pages || 1;

  const handleTabChange = (tab: typeof activeTab) => {
    setActiveTab(tab);
    setCurrentPage(1);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-gqt-neutral-200">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-gqt-blue/10 text-gqt-blue">
              <Bell className="w-6 h-6" />
            </div>
            <div>
              <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Notification Center</h1>
              <p className="text-sm text-gqt-neutral-600 mt-0.5">
                Real-time alerts, opportunity announcements, and workflow updates.
              </p>
            </div>
          </div>
        </div>

        {unreadCount > 0 && (
          <button
            type="button"
            onClick={() => markAllReadMutation.mutate()}
            disabled={markAllReadMutation.isPending}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold bg-gqt-blue text-white hover:bg-gqt-blue-dark transition-colors shadow-sm disabled:opacity-50"
          >
            <CheckCheck className="w-4 h-4" />
            Mark All as Read ({unreadCount})
          </button>
        )}
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2 pb-2">
        <button
          type="button"
          onClick={() => handleTabChange('all')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'all'
              ? 'bg-gqt-navy text-white shadow-sm'
              : 'bg-white text-gqt-neutral-600 hover:bg-gqt-neutral-100 border border-gqt-neutral-200'
          }`}
        >
          All Notifications
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('unread')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1.5 ${
            activeTab === 'unread'
              ? 'bg-gqt-navy text-white shadow-sm'
              : 'bg-white text-gqt-neutral-600 hover:bg-gqt-neutral-100 border border-gqt-neutral-200'
          }`}
        >
          Unread
          {unreadCount > 0 && (
            <span
              className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                activeTab === 'unread' ? 'bg-rose-500 text-white' : 'bg-rose-100 text-rose-700'
              }`}
            >
              {unreadCount}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('JOB_DRIVE')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'JOB_DRIVE'
              ? 'bg-gqt-navy text-white shadow-sm'
              : 'bg-white text-gqt-neutral-600 hover:bg-gqt-neutral-100 border border-gqt-neutral-200'
          }`}
        >
          Job Drives
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('APPLICATION')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'APPLICATION'
              ? 'bg-gqt-navy text-white shadow-sm'
              : 'bg-white text-gqt-neutral-600 hover:bg-gqt-neutral-100 border border-gqt-neutral-200'
          }`}
        >
          Applications
        </button>
        <button
          type="button"
          onClick={() => handleTabChange('FOLLOW_UP')}
          className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-colors ${
            activeTab === 'FOLLOW_UP'
              ? 'bg-gqt-navy text-white shadow-sm'
              : 'bg-white text-gqt-neutral-600 hover:bg-gqt-neutral-100 border border-gqt-neutral-200'
          }`}
        >
          Follow-ups
        </button>
      </div>

      {/* Main Content Area */}
      <div className="bg-white rounded-xl shadow-sm border border-gqt-neutral-200 overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 text-gqt-neutral-500">
            <RefreshCw className="w-8 h-8 animate-spin text-gqt-blue mb-3" />
            <p className="text-sm font-semibold">Loading notifications...</p>
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="w-12 h-12 rounded-full bg-rose-50 flex items-center justify-center text-rose-600 mb-3">
              <Filter className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-gqt-charcoal mb-1">Failed to load notifications</h3>
            <p className="text-xs text-gqt-neutral-500 max-w-sm mb-4">
              An error occurred while fetching your notifications. Please check your connection and try again.
            </p>
            <button
              type="button"
              onClick={() => refetch()}
              className="px-4 py-2 text-xs font-semibold text-white bg-gqt-blue hover:bg-gqt-blue-dark rounded-lg transition-colors"
            >
              Retry Request
            </button>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20 px-4 text-center">
            <div className="w-14 h-14 rounded-full bg-gqt-neutral-100 flex items-center justify-center text-gqt-neutral-400 mb-3">
              <Bell className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-gqt-navy">No notifications found</h3>
            <p className="text-xs text-gqt-neutral-500 mt-1 max-w-sm">
              {activeTab === 'unread'
                ? 'Great job! You have zero unread notifications.'
                : 'There are no notifications matching the selected filter criteria.'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gqt-neutral-100">
            {notifications.map((item: NotificationItem) => (
              <div
                key={item.id}
                className={`p-5 flex items-start gap-4 transition-colors hover:bg-gqt-neutral-50 ${
                  !item.is_read ? 'bg-gqt-blue/5' : ''
                }`}
              >
                <div className="p-2.5 rounded-xl bg-gqt-neutral-100 shrink-0 mt-0.5">
                  {getCategoryIcon(item.category)}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span
                      className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wider ${getCategoryBadgeClass(
                        item.category
                      )}`}
                    >
                      {item.category.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-gqt-neutral-400">
                      {new Date(item.created_at).toLocaleString()}
                    </span>
                    {!item.is_read && (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-gqt-blue text-white">
                        New
                      </span>
                    )}
                  </div>

                  <h3
                    className={`text-sm ${
                      !item.is_read ? 'font-bold text-gqt-navy' : 'font-semibold text-gqt-charcoal'
                    }`}
                  >
                    {item.title}
                  </h3>

                  <p className="text-xs text-gqt-neutral-600 mt-1 leading-relaxed whitespace-pre-line">
                    {item.message}
                  </p>

                  {item.link && (
                    <div className="mt-3">
                      <Link
                        to={item.link}
                        onClick={() => {
                          if (!item.is_read) markReadMutation.mutate(item.id);
                        }}
                        className="inline-flex items-center gap-1.5 text-xs font-semibold text-gqt-blue hover:text-gqt-blue-dark transition-colors"
                      >
                        Navigate to related workspace
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </div>
                  )}
                </div>

                <div className="shrink-0 flex items-center gap-2">
                  {!item.is_read ? (
                    <button
                      type="button"
                      onClick={() => markReadMutation.mutate(item.id)}
                      disabled={markReadMutation.isPending}
                      title="Mark as read"
                      className="p-2 text-gqt-neutral-400 hover:text-gqt-blue hover:bg-gqt-neutral-200/50 rounded-lg transition-colors border border-gqt-neutral-200"
                    >
                      <Check className="w-4 h-4" />
                    </button>
                  ) : (
                    <span className="text-xs font-medium text-gqt-neutral-400 flex items-center gap-1">
                      <CheckCheck className="w-3.5 h-3.5 text-gqt-neutral-400" />
                      Read
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination Bar */}
        {meta && totalPages > 1 && (
          <div className="px-6 py-4 bg-gqt-neutral-50/80 border-t border-gqt-neutral-200 flex items-center justify-between">
            <span className="text-xs text-gqt-neutral-500 font-medium">
              Showing page <span className="font-bold text-gqt-navy">{meta.current_page}</span> of{' '}
              <span className="font-bold text-gqt-navy">{meta.total_pages}</span> ({meta.count} total)
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage <= 1 || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border border-gqt-neutral-300 bg-white text-gqt-charcoal hover:bg-gqt-neutral-50 disabled:opacity-40 transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </button>
              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage >= totalPages || isLoading}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-semibold border border-gqt-neutral-300 bg-white text-gqt-charcoal hover:bg-gqt-neutral-50 disabled:opacity-40 transition-colors"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

