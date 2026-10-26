import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  PhoneCall,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Plus,
  ArrowUpRight,
  TrendingUp,
} from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';

export const CrmDashboardPage: React.FC = () => {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['crm-dashboard-metrics'],
    queryFn: () => crmApi.getDashboardMetrics(),
  });

  if (isLoading) {
    return (
      <div className="py-12">
        <LoadingState message="Loading Corporate CRM operational metrics..." />
      </div>
    );
  }

  if (error || !data?.success) {
    return (
      <div className="py-8">
        <ErrorState
          title="Failed to Load CRM Metrics"
          message={error instanceof Error ? error.message : 'Could not retrieve operational metrics.'}
          onRetry={() => refetch()}
        />
      </div>
    );
  }

  const metrics = data.data;

  return (
    <div className="space-y-8">
      {/* Header & Quick Action Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-gqt-navy tracking-tight">
            Corporate CRM & HR Directory
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Corporate outreach management, HR relationship nurturing, and 100+ outreach/day target tracking.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link to="/crm/companies/new">
            <Button size="sm" variant="outline" leftIcon={<Building2 className="w-4 h-4" />}>
              Add Company
            </Button>
          </Link>
          <Link to="/crm/contacts/new">
            <Button size="sm" variant="outline" leftIcon={<Users className="w-4 h-4" />}>
              Add Contact
            </Button>
          </Link>
          <Link to="/crm/outreach/new">
            <Button size="sm" variant="primary" leftIcon={<PhoneCall className="w-4 h-4" />}>
              Log Outreach
            </Button>
          </Link>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <Card className="p-5 border-l-4 border-l-gqt-blue">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gqt-neutral-500 uppercase tracking-wider">
              Active Companies
            </span>
            <Building2 className="w-5 h-5 text-gqt-blue" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-black text-gqt-navy tracking-tight">
              {metrics.total_active_companies}
            </span>
            <Link
              to="/crm/companies"
              className="text-xs font-semibold text-gqt-blue hover:text-gqt-blue-dark flex items-center gap-0.5"
            >
              View directory <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <p className="text-xs text-gqt-neutral-500 mt-2">Verified enterprise hiring partners</p>
        </Card>

        <Card className="p-5 border-l-4 border-l-emerald-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gqt-neutral-500 uppercase tracking-wider">
              Active HR Contacts
            </span>
            <Users className="w-5 h-5 text-emerald-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-black text-gqt-navy tracking-tight">
              {metrics.total_active_contacts}
            </span>
            <Link
              to="/crm/contacts"
              className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-0.5"
            >
              View contacts <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <p className="text-xs text-gqt-neutral-500 mt-2">Recruiters and TA decision makers</p>
        </Card>

        <Card className="p-5 border-l-4 border-l-amber-500">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gqt-neutral-500 uppercase tracking-wider">
              Follow-ups Due Today
            </span>
            <Calendar className="w-5 h-5 text-amber-600" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className="text-3xl font-black text-gqt-navy tracking-tight">
              {metrics.follow_ups_due_today}
            </span>
            <Link
              to="/crm/follow-ups?tab=today"
              className="text-xs font-semibold text-amber-600 hover:text-amber-700 flex items-center gap-0.5"
            >
              Open worklist <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <p className="text-xs text-gqt-neutral-500 mt-2">Scheduled touchpoints today</p>
        </Card>

        <Card className={`p-5 border-l-4 ${metrics.follow_ups_overdue > 0 ? 'border-l-red-500 bg-red-50/30' : 'border-l-gqt-neutral-300'}`}>
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-gqt-neutral-500 uppercase tracking-wider">
              Overdue Tasks
            </span>
            <AlertTriangle className={`w-5 h-5 ${metrics.follow_ups_overdue > 0 ? 'text-red-600' : 'text-gqt-neutral-400'}`} />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <span className={`text-3xl font-black tracking-tight ${metrics.follow_ups_overdue > 0 ? 'text-red-600' : 'text-gqt-navy'}`}>
              {metrics.follow_ups_overdue}
            </span>
            <Link
              to="/crm/follow-ups?tab=overdue"
              className={`text-xs font-semibold flex items-center gap-0.5 ${metrics.follow_ups_overdue > 0 ? 'text-red-600 hover:text-red-700' : 'text-gqt-neutral-500'}`}
            >
              Action queue <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <p className="text-xs text-gqt-neutral-500 mt-2">Breached due-date follow-ups</p>
        </Card>
      </div>

      {/* Operational Target Banner: 100+ Outreach/Day */}
      <Card className="p-6 bg-gradient-to-r from-gqt-navy to-gqt-navy-dark text-white shadow-md">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-1.5 max-w-xl">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-gqt-blue text-white">
                Operational Target
              </span>
              <span className="text-xs text-gqt-neutral-300">
                Workflow Step 2 Benchmark: 100+ Touchpoints / Day
              </span>
            </div>
            <h2 className="text-xl font-bold tracking-tight">Daily Outreach Benchmark</h2>
            <p className="text-sm text-gqt-neutral-300 leading-relaxed">
              Track multi-channel corporate outreach across phone calls, emails, LinkedIn inmails, and WhatsApp touchpoints.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">
            <div className="text-center sm:text-right">
              <div className="text-4xl font-black text-white tracking-tight">
                {metrics.today_outreach_count}{' '}
                <span className="text-lg font-normal text-gqt-neutral-400">/ {metrics.daily_outreach_target}</span>
              </div>
              <p className="text-xs text-gqt-neutral-300 mt-1">
                Completed today ({metrics.today_outreach_progress_percent}% of target)
              </p>
            </div>

            <Link to="/crm/outreach/new">
              <Button size="md" className="bg-white text-gqt-navy hover:bg-gqt-neutral-100 font-bold border-none">
                <Plus className="w-4 h-4 mr-1.5 text-gqt-blue" />
                Log Completed Outreach
              </Button>
            </Link>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-5 w-full bg-gqt-navy-light/60 rounded-full h-3 overflow-hidden border border-white/10">
          <div
            className="bg-gradient-to-r from-gqt-blue to-emerald-400 h-full rounded-full transition-all duration-500 ease-out"
            style={{ width: `${Math.min(100, metrics.today_outreach_progress_percent)}%` }}
          />
        </div>
      </Card>

      {/* Grid: Outreach Channels & Recent Activities */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Channel Breakdown */}
        <Card className="p-6">
          <h3 className="text-base font-bold text-gqt-navy mb-4 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-gqt-blue" />
            Today's Outreach by Channel
          </h3>
          <div className="space-y-3.5">
            {[
              { label: 'Phone Calls', key: 'CALL', color: 'bg-blue-500' },
              { label: 'Emails', key: 'EMAIL', color: 'bg-indigo-500' },
              { label: 'LinkedIn', key: 'LINKEDIN', color: 'bg-sky-500' },
              { label: 'WhatsApp', key: 'WHATSAPP', color: 'bg-emerald-500' },
              { label: 'In-Person', key: 'IN_PERSON', color: 'bg-purple-500' },
            ].map((channel) => {
              const count = metrics.channel_breakdown[channel.key] || 0;
              const pct = metrics.today_outreach_count > 0 ? Math.round((count / metrics.today_outreach_count) * 100) : 0;
              return (
                <div key={channel.key} className="space-y-1">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-gqt-charcoal">{channel.label}</span>
                    <span className="text-gqt-neutral-600">
                      {count} ({pct}%)
                    </span>
                  </div>
                  <div className="w-full bg-gqt-neutral-100 rounded-full h-2 overflow-hidden">
                    <div className={`${channel.color} h-full rounded-full`} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="mt-6 pt-4 border-t border-gqt-neutral-100 text-xs text-gqt-neutral-500">
            Your logged touchpoints today: <strong className="text-gqt-navy">{metrics.user_today_outreach_count}</strong>
          </div>
        </Card>

        {/* Recent Activities Feed */}
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              Recent Corporate Touchpoints
            </h3>
            <Link to="/crm/outreach" className="text-xs font-semibold text-gqt-blue hover:text-gqt-blue-dark">
              View all history &rarr;
            </Link>
          </div>

          {metrics.recent_activities.length === 0 ? (
            <div className="py-8 text-center text-sm text-gqt-neutral-500">
              No outreach touchpoints logged yet today.
            </div>
          ) : (
            <div className="divide-y divide-gqt-neutral-100 max-h-96 overflow-y-auto">
              {metrics.recent_activities.map((item) => (
                <div key={item.id} className="py-3 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-neutral-700">
                        {item.channel}
                      </span>
                      <Link
                        to={`/crm/companies/${item.company__id}`}
                        className="text-sm font-semibold text-gqt-navy hover:text-gqt-blue transition-colors"
                      >
                        {item.company__name}
                      </Link>
                    </div>
                    {item.subject && <p className="text-xs text-gqt-charcoal">{item.subject}</p>}
                    <p className="text-[11px] text-gqt-neutral-500">
                      Outcome: <strong className="text-gqt-neutral-700">{item.outcome}</strong> • By{' '}
                      {item.performed_by__first_name || item.performed_by__email}
                    </p>
                  </div>
                  <span className="text-[11px] text-gqt-neutral-400 whitespace-nowrap">
                    {new Date(item.activity_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};
