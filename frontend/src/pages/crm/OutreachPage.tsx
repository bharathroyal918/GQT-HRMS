import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { PhoneCall, Search, Building2, Users } from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { EmptyState } from '../../components/common/EmptyState';

export const OutreachPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [channel, setChannel] = useState('');
  const [outcome, setOutcome] = useState('');
  const [direction, setDirection] = useState('');
  const [page, setPage] = useState(1);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['outreach-logs', { search, channel, outcome, direction, page }],
    queryFn: () =>
      crmApi.getOutreachLogs({
        search: search || undefined,
        channel: channel || undefined,
        outcome: outcome || undefined,
        direction: direction || undefined,
        page,
        page_size: 15,
      }),
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-gqt-navy tracking-tight">Corporate Outreach History</h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Audit-logged multi-channel touchpoints contributing to the 100+ outreach/day target (Workflow Step 2).
          </p>
        </div>
        <Link to="/crm/outreach/new">
          <Button variant="primary" size="sm" leftIcon={<PhoneCall className="w-4 h-4" />}>
            Log Completed Outreach
          </Button>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <Card className="p-4 bg-white">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gqt-neutral-400" />
            <input
              type="text"
              placeholder="Search by company, HR contact, subject..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue"
            />
          </div>

          <div>
            <select
              value={channel}
              onChange={(e) => {
                setChannel(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Channels</option>
              <option value="CALL">Phone Call</option>
              <option value="EMAIL">Email</option>
              <option value="LINKEDIN">LinkedIn</option>
              <option value="WHATSAPP">WhatsApp</option>
              <option value="IN_PERSON">In-Person Visit</option>
            </select>
          </div>

          <div>
            <select
              value={direction}
              onChange={(e) => {
                setDirection(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Directions</option>
              <option value="OUTBOUND">Outbound</option>
              <option value="INBOUND">Inbound</option>
            </select>
          </div>

          <div>
            <select
              value={outcome}
              onChange={(e) => {
                setOutcome(e.target.value);
                setPage(1);
              }}
              className="w-full py-2 px-3 text-xs border border-gqt-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-gqt-blue text-gqt-charcoal bg-white"
            >
              <option value="">All Outcomes</option>
              <option value="CONNECTED_INTERESTED">Connected — Interested</option>
              <option value="CONNECTED_NOT_INTERESTED">Connected — Not Interested</option>
              <option value="CONNECTED_CALL_LATER">Connected — Callback</option>
              <option value="NO_ANSWER_BUSY">No Answer / Busy</option>
              <option value="INVALID_CONTACT_DETAILS">Invalid Details</option>
              <option value="FOLLOW_UP_SCHEDULED">Follow-Up Scheduled</option>
              <option value="REQUIREMENT_COLLECTED">JD / Requirement Collected</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Outreach Stream Content */}
      {isLoading ? (
        <LoadingState message="Loading outreach logs..." />
      ) : error ? (
        <ErrorState
          title="Could not load outreach logs"
          message={error instanceof Error ? error.message : 'Network error'}
          onRetry={() => refetch()}
        />
      ) : !data || data.data.length === 0 ? (
        <EmptyState
          title="No Outreach Records"
          description="No touchpoints match your filter. Log your outreach interactions to track the daily target."
          action={
            <Link to="/crm/outreach/new">
              <Button size="sm" variant="primary">
                Log First Outreach
              </Button>
            </Link>
          }
        />
      ) : (
        <Card className="divide-y divide-gqt-neutral-100 overflow-hidden">
          {data.data.map((log) => (
            <div key={log.id} className="p-4 flex flex-col sm:flex-row sm:items-start justify-between gap-4 hover:bg-gqt-neutral-50/50 transition-colors">
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-blue-light text-gqt-blue">
                    {log.channel}
                  </span>
                  <span className="text-[11px] font-semibold text-gqt-neutral-500 uppercase">
                    {log.direction}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      log.outcome.includes('INTERESTED') || log.outcome.includes('COLLECTED')
                        ? 'bg-emerald-100 text-emerald-800'
                        : log.outcome.includes('BUSY') || log.outcome.includes('INVALID')
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-gqt-neutral-100 text-gqt-neutral-700'
                    }`}
                  >
                    {log.outcome.replace(/_/g, ' ')}
                  </span>
                  {log.followup_required && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-purple-100 text-purple-700">
                      Follow-up Required
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3">
                  <Link
                    to={`/crm/companies/${log.company.id}`}
                    className="text-sm font-bold text-gqt-navy hover:underline flex items-center gap-1"
                  >
                    <Building2 className="w-3.5 h-3.5 text-gqt-blue" />
                    {log.company.name}
                  </Link>
                  {log.hr_contact && (
                    <span className="text-xs text-gqt-charcoal flex items-center gap-1 font-medium">
                      <Users className="w-3.5 h-3.5 text-emerald-600" />
                      {log.hr_contact.name} ({log.hr_contact.designation})
                    </span>
                  )}
                </div>

                {log.subject && <p className="text-xs font-semibold text-gqt-charcoal">{log.subject}</p>}
                {log.notes && <p className="text-xs text-gqt-neutral-600 leading-relaxed">{log.notes}</p>}

                <p className="text-[11px] text-gqt-neutral-400">
                  Logged by <strong>{log.performed_by.full_name || log.performed_by.email}</strong> on{' '}
                  {new Date(log.activity_date).toLocaleString()}
                </p>
              </div>
            </div>
          ))}

          {/* Pagination */}
          {data.meta.total_pages > 1 && (
            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-between text-xs text-gqt-neutral-600">
              <div>
                Page {data.meta.current_page} of {data.meta.total_pages} ({data.meta.count} total)
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!data.meta.previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={!data.meta.next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
