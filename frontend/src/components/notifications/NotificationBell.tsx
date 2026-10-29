import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
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
  RefreshCw,
  ExternalLink,
} from 'lucide-react';
import { notificationsApi } from '@/api/notificationsApi';
import { NotificationCategory, NotificationItem } from '@/types/notifications';

const getCategoryIcon = (category: NotificationCategory) => {
  switch (category) {
    case 'JOB_DRIVE':
      return <Briefcase className="w-4 h-4 text-gqt-blue" />;
    case 'APPLICATION':
      return <Send className="w-4 h-4 text-emerald-600" />;
    case 'INTERVIEW':
      return <Calendar className="w-4 h-4 text-indigo-600" />;
    case 'PLACEMENT':
      return <Award className="w-4 h-4 text-amber-600" />;
    case 'FOLLOW_UP':
      return <PhoneCall className="w-4 h-4 text-purple-600" />;
    case 'SYSTEM':
    default:
      return <Info className="w-4 h-4 text-gqt-neutral-500" />;
  }
};

const formatTimeAgo = (dateStr: string) => {
  try {
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return 'just now';
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHrs = Math.floor(diffMin / 60);
    if (diffHrs < 24) return `${diffHrs}h ago`;
    const diffDays = Math.floor(diffHrs / 24);
    return `${diffDays}d ago`;
  } catch {
    return '';
  }
};

export const NotificationBell: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  // Query unread count
  const { data: countData } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => notificationsApi.getUnreadCount(),
    refetchOnWindowFocus: true,
  });

  const unreadCount = countData?.count ?? 0;

  // Query recent notifications (fetch when open or pre-warm)
  const {
    data: notificationsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['notifications', 'recent'],
    queryFn: () => notificationsApi.listNotifications({ page: 1, page_size: 6 }),
    enabled: isOpen,
  });

  // Mark single notification read
  const markReadMutation = useMutation({
    mutationFn: (id: string) => notificationsApi.markAsRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Mark all notifications read
  const markAllReadMutation = useMutation({
    mutationFn: () => notificationsApi.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });

  // Close dropdown on outside click or Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleNotificationClick = (item: NotificationItem) => {
    if (!item.is_read) {
      markReadMutation.mutate(item.id);
    }
    if (item.link) {
      setIsOpen(false);
      navigate(item.link);
    }
  };

  const notifications = notificationsData?.data || [];

  return (
    <div className="relative inline-block text-left" ref={dropdownRef}>
      {/* Bell Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-label="Notifications"
        aria-expanded={isOpen}
        aria-haspopup="true"
        className="relative p-2 text-gqt-neutral-600 hover:text-gqt-navy hover:bg-gqt-neutral-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-gqt-blue"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span
            data-testid="unread-badge"
            className="absolute top-1 right-1 flex items-center justify-center min-w-4 h-4 px-1 text-[10px] font-bold text-white bg-rose-600 rounded-full shadow-sm"
          >
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div
          data-testid="notifications-dropdown"
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-xl shadow-xl border border-gqt-neutral-200 z-50 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-gqt-neutral-50/80 border-b border-gqt-neutral-200">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-gqt-navy">Notifications</h3>
              {unreadCount > 0 && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-gqt-blue/10 text-gqt-blue rounded-full">
                  {unreadCount} unread
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                type="button"
                onClick={() => markAllReadMutation.mutate()}
                disabled={markAllReadMutation.isPending}
                className="inline-flex items-center gap-1 text-xs font-medium text-gqt-blue hover:text-gqt-blue-dark transition-colors disabled:opacity-50"
              >
                <CheckCheck className="w-3.5 h-3.5" />
                Mark all read
              </button>
            )}
          </div>

          {/* Body */}
          <div className="max-h-80 overflow-y-auto divide-y divide-gqt-neutral-100">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-8 text-gqt-neutral-500">
                <RefreshCw className="w-5 h-5 animate-spin mb-2 text-gqt-blue" />
                <span className="text-xs">Loading notifications...</span>
              </div>
            ) : isError ? (
              <div className="flex flex-col items-center justify-center py-6 px-4 text-center">
                <p className="text-xs text-rose-600 mb-2">Failed to load notifications.</p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="px-3 py-1 text-xs font-semibold text-gqt-blue bg-gqt-blue-light hover:bg-gqt-blue/20 rounded transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center px-4">
                <div className="w-10 h-10 rounded-full bg-gqt-neutral-100 flex items-center justify-center mb-2 text-gqt-neutral-400">
                  <Bell className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-gqt-charcoal">No notifications</p>
                <p className="text-[11px] text-gqt-neutral-500 mt-0.5">
                  You are all caught up with your updates.
                </p>
              </div>
            ) : (
              notifications.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleNotificationClick(item)}
                  className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-gqt-neutral-50 ${!item.is_read ? 'bg-gqt-blue/5' : ''
                    }`}
                >
                  <div className="p-2 rounded-lg bg-gqt-neutral-100 shrink-0 mt-0.5">
                    {getCategoryIcon(item.category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <p
                        className={`text-xs truncate ${!item.is_read ? 'font-bold text-gqt-navy' : 'font-medium text-gqt-charcoal'
                          }`}
                      >
                        {item.title}
                      </p>
                      {!item.is_read && (
                        <span className="w-2 h-2 rounded-full bg-gqt-blue shrink-0" />
                      )}
                    </div>
                    <p className="text-[11px] text-gqt-neutral-600 line-clamp-2 mt-0.5 leading-relaxed">
                      {item.message}
                    </p>
                    <div className="flex items-center justify-between mt-1 text-[10px] text-gqt-neutral-400">
                      <span>{formatTimeAgo(item.created_at)}</span>
                      {item.link && (
                        <span className="inline-flex items-center gap-0.5 text-gqt-blue hover:underline">
                          View details
                          <ExternalLink className="w-2.5 h-2.5" />
                        </span>
                      )}
                    </div>
                  </div>
                  {!item.is_read && (
                    <button
                      type="button"
                      title="Mark as read"
                      onClick={(e) => {
                        e.stopPropagation();
                        markReadMutation.mutate(item.id);
                      }}
                      className="p-1 text-gqt-neutral-400 hover:text-gqt-blue hover:bg-gqt-neutral-200/50 rounded transition-colors shrink-0 mt-0.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 bg-gqt-neutral-50 border-t border-gqt-neutral-200 text-center">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-semibold text-gqt-blue hover:text-gqt-blue-dark transition-colors inline-flex items-center gap-1"
            >
              View all notifications
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
