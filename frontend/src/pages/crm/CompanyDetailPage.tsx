import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  Users,
  PhoneCall,
  Calendar,
  ExternalLink,
  Edit,
  ArrowLeft,
  Mail,
  Phone,
  Activity,
  Award,
  Briefcase,
  Send,
  Star,
} from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { Card } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';

export const CompanyDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<'contacts' | 'outreach' | 'followups' | 'notes' | 'profile360' | 'timeline'>('profile360');

  const { data: company, isLoading, error, refetch } = useQuery({
    queryKey: ['company-detail', id],
    queryFn: () => (id ? crmApi.getCompany(id) : null),
    enabled: Boolean(id),
  });

  const { data: profile360Data, isLoading: is360Loading } = useQuery({
    queryKey: ['company-360', id],
    queryFn: () => (id ? crmApi.getCompany360(id) : null),
    enabled: Boolean(id) && activeTab === 'profile360',
  });

  const { data: timelineData, isLoading: isTimelineLoading } = useQuery({
    queryKey: ['company-timeline', id],
    queryFn: () => (id ? crmApi.getCompanyTimeline(id) : null),
    enabled: Boolean(id) && activeTab === 'timeline',
  });

  const { data: outreachLogs } = useQuery({
    queryKey: ['company-outreach', id],
    queryFn: () => (id ? crmApi.getOutreachLogs({ company_id: id }) : null),
    enabled: Boolean(id) && activeTab === 'outreach',
  });

  const { data: followUps } = useQuery({
    queryKey: ['company-follow-ups', id],
    queryFn: () => (id ? crmApi.getFollowUps({ company_id: id }) : null),
    enabled: Boolean(id) && activeTab === 'followups',
  });

  if (isLoading) {
    return <LoadingState message="Loading company profile and relationship history..." />;
  }

  if (error || !company) {
    return (
      <ErrorState
        title="Could not find company profile"
        message={error instanceof Error ? error.message : 'Company record does not exist or has been removed.'}
        onRetry={() => refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Navigation & Actions */}
      <div className="flex items-center justify-between">
        <Link
          to="/crm/companies"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-gqt-neutral-600 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to Companies Directory
        </Link>
        <div className="flex gap-2">
          <Link to={`/crm/companies/${company.id}/edit`}>
            <Button size="sm" variant="outline" leftIcon={<Edit className="w-3.5 h-3.5" />}>
              Edit Profile
            </Button>
          </Link>
          <Link to={`/crm/outreach/new?company_id=${company.id}`}>
            <Button size="sm" variant="primary" leftIcon={<PhoneCall className="w-3.5 h-3.5" />}>
              Log Outreach
            </Button>
          </Link>
        </div>
      </div>

      {/* Overview Banner Card */}
      <Card className="p-6 border-l-4 border-l-gqt-blue">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="px-2.5 py-0.5 rounded text-xs font-bold uppercase bg-gqt-blue-light text-gqt-blue">
                {company.domain_category.replace(/_/g, ' ')}
              </span>
              <StatusBadge
                variant={
                  company.relationship_status === 'ACTIVE_HIRING_PARTNER'
                    ? 'success'
                    : company.relationship_status === 'CONNECTED' || company.relationship_status === 'INTERESTED'
                    ? 'info'
                    : company.relationship_status === 'NOT_INTERESTED'
                    ? 'danger'
                    : company.relationship_status === 'ON_HOLD'
                    ? 'warning'
                    : 'neutral'
                }
                label={company.relationship_status.replace(/_/g, ' ')}
              />
              <span className="text-xs font-medium text-gqt-neutral-500">
                {company.tier === 'TIER_1' ? 'Tier 1 Enterprise' : company.tier === 'TIER_2' ? 'Tier 2 Mid-Market' : 'Tier 3 Startup'}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-gqt-navy tracking-tight">{company.name}</h1>

            <div className="flex flex-wrap items-center gap-4 text-xs text-gqt-neutral-600">
              {company.website && (
                <a
                  href={company.website}
                  target="_blank"
                  rel="noreferrer"
                  className="text-gqt-blue hover:underline flex items-center gap-1 font-semibold"
                >
                  {company.domain || company.website} <ExternalLink className="w-3 h-3" />
                </a>
              )}
              {company.city && <span>📍 {company.city}, {company.country}</span>}
              <span>Owner: <strong>{company.owner?.full_name || 'Unassigned'}</strong></span>
            </div>
          </div>

          <div className="flex sm:flex-col items-center sm:items-end justify-between gap-4 border-t sm:border-t-0 pt-4 sm:pt-0 border-gqt-neutral-100 text-right">
            <div className="text-center sm:text-right">
              <span className="text-2xl font-black text-gqt-navy">{company.hr_contacts?.length || 0}</span>
              <p className="text-[11px] text-gqt-neutral-500">HR Contacts</p>
            </div>
            <div className="text-center sm:text-right">
              <span className="text-2xl font-black text-gqt-navy">{company.open_follow_ups_count || 0}</span>
              <p className="text-[11px] text-gqt-neutral-500">Open Follow-ups</p>
            </div>
          </div>
        </div>
      </Card>

      {/* Tabs */}
      <div className="border-b border-gqt-neutral-200">
        <nav className="flex gap-6 -mb-px text-xs font-bold uppercase tracking-wider">
          <button
            onClick={() => setActiveTab('profile360')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'profile360'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Activity className="w-4 h-4" /> 360° Recruitment Summary
          </button>
          <button
            onClick={() => setActiveTab('timeline')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'timeline'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Send className="w-4 h-4" /> Communication Timeline
          </button>
          <button
            onClick={() => setActiveTab('contacts')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'contacts'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Users className="w-4 h-4" /> HR Contacts ({company.hr_contacts?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('outreach')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'outreach'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <PhoneCall className="w-4 h-4" /> Outreach History
          </button>
          <button
            onClick={() => setActiveTab('followups')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'followups'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            <Calendar className="w-4 h-4" /> Follow-ups ({company.open_follow_ups_count || 0})
          </button>
          <button
            onClick={() => setActiveTab('notes')}
            className={`py-3 flex items-center gap-2 border-b-2 transition-colors ${
              activeTab === 'notes'
                ? 'border-gqt-blue text-gqt-blue'
                : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
            }`}
          >
            Notes & Details
          </button>
        </nav>
      </div>

      {/* Tab Panels */}
      {activeTab === 'contacts' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-gqt-navy">HR Talent Directory</h3>
            <Link to={`/crm/contacts/new?company_id=${company.id}`}>
              <Button size="sm" variant="outline" leftIcon={<Users className="w-3.5 h-3.5" />}>
                Add HR Contact
              </Button>
            </Link>
          </div>

          {!company.hr_contacts || company.hr_contacts.length === 0 ? (
            <Card className="p-8 text-center text-xs text-gqt-neutral-500">
              No HR contacts registered for this company yet. Click &quot;Add HR Contact&quot; to register recruiters.
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {company.hr_contacts.map((contact) => (
                <Card key={contact.id} className="p-4 hover:border-gqt-neutral-300 transition-colors">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-gqt-navy">{contact.name}</h4>
                      <p className="text-xs text-gqt-neutral-600 font-medium">{contact.designation || 'HR Representative'}</p>
                    </div>
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-neutral-700">
                      {contact.status}
                    </span>
                  </div>
                  <div className="mt-3 space-y-1 text-xs text-gqt-charcoal">
                    {contact.email && (
                      <div className="flex items-center gap-2">
                        <Mail className="w-3.5 h-3.5 text-gqt-neutral-400" />
                        <a href={`mailto:${contact.email}`} className="text-gqt-blue hover:underline">
                          {contact.email}
                        </a>
                      </div>
                    )}
                    {contact.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-3.5 h-3.5 text-gqt-neutral-400" />
                        <span>{contact.phone}</span>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'outreach' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-gqt-navy">Touchpoint Activity History</h3>
            <Link to={`/crm/outreach/new?company_id=${company.id}`}>
              <Button size="sm" variant="primary" leftIcon={<PhoneCall className="w-3.5 h-3.5" />}>
                Log Touchpoint
              </Button>
            </Link>
          </div>

          {!outreachLogs || outreachLogs.data.length === 0 ? (
            <Card className="p-8 text-center text-xs text-gqt-neutral-500">
              No outreach activities logged for this company yet.
            </Card>
          ) : (
            <Card className="divide-y divide-gqt-neutral-100">
              {outreachLogs.data.map((log) => (
                <div key={log.id} className="p-4 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-blue-light text-gqt-blue">
                        {log.channel}
                      </span>
                      <span className="text-xs font-semibold text-gqt-charcoal">
                        {log.direction} • {log.outcome.replace(/_/g, ' ')}
                      </span>
                    </div>
                    {log.subject && <p className="text-sm font-bold text-gqt-navy">{log.subject}</p>}
                    {log.notes && <p className="text-xs text-gqt-neutral-600">{log.notes}</p>}
                    <p className="text-[11px] text-gqt-neutral-400">
                      By {log.performed_by.full_name} • {new Date(log.activity_date).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>
      )}

      {activeTab === 'followups' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="text-sm font-bold text-gqt-navy">Scheduled Corporate Tasks</h3>
            <Link to={`/crm/follow-ups`}>
              <Button size="sm" variant="outline" leftIcon={<Calendar className="w-3.5 h-3.5" />}>
                View Follow-ups Workspace
              </Button>
            </Link>
          </div>

          {!followUps || followUps.data.length === 0 ? (
            <Card className="p-8 text-center text-xs text-gqt-neutral-500">
              No follow-ups recorded for this company.
            </Card>
          ) : (
            <div className="space-y-3">
              {followUps.data.map((f) => (
                <Card key={f.id} className={`p-4 ${f.is_overdue ? 'border-red-300 bg-red-50/20' : ''}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${f.is_overdue ? 'bg-red-100 text-red-700' : 'bg-gqt-neutral-100 text-gqt-neutral-700'}`}>
                          {f.is_overdue ? 'OVERDUE' : f.status}
                        </span>
                        <span className="text-xs font-bold text-gqt-navy">{f.priority} Priority</span>
                      </div>
                      <h4 className="text-sm font-bold text-gqt-navy mt-1.5">{f.purpose}</h4>
                      <p className="text-xs text-gqt-neutral-500 mt-1">
                        Due: {new Date(f.due_date).toLocaleString()} • Assigned to: {f.assigned_to.full_name}
                      </p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'notes' && (
        <Card className="p-6 space-y-4 text-xs">
          <div>
            <h4 className="font-bold text-gqt-navy uppercase tracking-wider mb-1">Corporate Address</h4>
            <p className="text-gqt-charcoal whitespace-pre-wrap">{company.address || 'No address specified.'}</p>
          </div>
          <div className="pt-4 border-t border-gqt-neutral-100">
            <h4 className="font-bold text-gqt-navy uppercase tracking-wider mb-1">Internal Notes</h4>
            <p className="text-gqt-charcoal whitespace-pre-wrap">{company.notes || 'No internal notes recorded.'}</p>
          </div>
          <div className="pt-4 border-t border-gqt-neutral-100 text-gqt-neutral-400 space-y-1">
            <p>Created by: {company.created_by?.full_name || 'System'} on {new Date(company.created_at).toLocaleDateString()}</p>
            <p>Last modified on {new Date(company.updated_at).toLocaleDateString()}</p>
          </div>
        </Card>
      )}

      {/* 360-Degree Recruitment Summary Tab */}
      {activeTab === 'profile360' && (
        <div className="space-y-6">
          {is360Loading ? (
            <LoadingState message="Aggregating 360° hiring metrics and drive history..." />
          ) : !profile360Data?.data ? (
            <Card className="p-8 text-center text-xs text-gqt-neutral-500">
              No recruitment activity recorded for this corporate partner yet.
            </Card>
          ) : (
            <>
              {/* Lifetime Metrics Row */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Total Drives</span>
                  <p className="text-xl font-extrabold text-gqt-navy mt-1">
                    {profile360Data.data.lifetime_metrics.total_jobs}
                  </p>
                </Card>
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Submissions</span>
                  <p className="text-xl font-extrabold text-gqt-navy mt-1">
                    {profile360Data.data.lifetime_metrics.total_submissions}
                  </p>
                </Card>
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Interviewed</span>
                  <p className="text-xl font-extrabold text-gqt-navy mt-1">
                    {profile360Data.data.lifetime_metrics.total_interviewed}
                  </p>
                </Card>
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Selected</span>
                  <p className="text-xl font-extrabold text-emerald-600 mt-1">
                    {profile360Data.data.lifetime_metrics.total_placed}
                  </p>
                </Card>
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Joined</span>
                  <p className="text-xl font-extrabold text-blue-600 mt-1">
                    {profile360Data.data.lifetime_metrics.total_joined}
                  </p>
                </Card>
                <Card className="p-3 text-center bg-white border border-gqt-neutral-200">
                  <span className="text-[10px] font-bold uppercase text-gqt-neutral-500">Avg Offered CTC</span>
                  <p className="text-base font-extrabold text-gqt-navy mt-1">
                    {profile360Data.data.lifetime_metrics.avg_offered_ctc > 0
                      ? `₹${(profile360Data.data.lifetime_metrics.avg_offered_ctc / 100000).toFixed(2)} LPA`
                      : 'N/A'}
                  </p>
                </Card>
              </div>

              {/* Feedback & Satisfaction Summary */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="p-5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-3 flex items-center gap-1.5">
                    <Star className="w-4 h-4 text-amber-500" />
                    Corporate HR Evaluations Summary
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div className="flex justify-between items-center py-1 border-b border-gqt-neutral-100">
                      <span className="text-gqt-neutral-600">Total Evaluations Received</span>
                      <strong className="text-gqt-navy">{profile360Data.data.feedback_summary.total_hr_evaluations}</strong>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gqt-neutral-100">
                      <span className="text-gqt-neutral-600">Average Technical Skills Rating</span>
                      <strong className="text-gqt-navy">
                        {profile360Data.data.feedback_summary.avg_technical_skills_rating > 0
                          ? `${profile360Data.data.feedback_summary.avg_technical_skills_rating} / 5.0`
                          : 'Not Rated'}
                      </strong>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-gqt-neutral-100">
                      <span className="text-gqt-neutral-600">Average Communication Skills Rating</span>
                      <strong className="text-gqt-navy">
                        {profile360Data.data.feedback_summary.avg_communication_skills_rating > 0
                          ? `${profile360Data.data.feedback_summary.avg_communication_skills_rating} / 5.0`
                          : 'Not Rated'}
                      </strong>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-gqt-neutral-600">Overall Hiring Satisfaction</span>
                      <strong className="text-emerald-700">
                        {profile360Data.data.feedback_summary.avg_hiring_satisfaction_rating > 0
                          ? `${profile360Data.data.feedback_summary.avg_hiring_satisfaction_rating} / 5.0`
                          : 'Not Rated'}
                      </strong>
                    </div>
                  </div>
                </Card>

                <Card className="p-5">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-3 flex items-center gap-1.5">
                    <Activity className="w-4 h-4 text-gqt-blue" />
                    Student Candidate Interview Experience
                  </h4>
                  <p className="text-[11px] text-gqt-neutral-500 mb-3">
                    Aggregated anonymous candidate ratings across interview difficulty.
                  </p>
                  <div className="grid grid-cols-4 gap-2 text-center text-xs">
                    <div className="p-2 rounded bg-emerald-50 text-emerald-800">
                      <span className="text-[10px] font-bold uppercase">Easy</span>
                      <p className="text-lg font-bold">{profile360Data.data.feedback_summary.difficulty_breakdown.EASY || 0}</p>
                    </div>
                    <div className="p-2 rounded bg-blue-50 text-blue-800">
                      <span className="text-[10px] font-bold uppercase">Medium</span>
                      <p className="text-lg font-bold">{profile360Data.data.feedback_summary.difficulty_breakdown.MEDIUM || 0}</p>
                    </div>
                    <div className="p-2 rounded bg-amber-50 text-amber-800">
                      <span className="text-[10px] font-bold uppercase">Hard</span>
                      <p className="text-lg font-bold">{profile360Data.data.feedback_summary.difficulty_breakdown.HARD || 0}</p>
                    </div>
                    <div className="p-2 rounded bg-rose-50 text-rose-800">
                      <span className="text-[10px] font-bold uppercase">Very Hard</span>
                      <p className="text-lg font-bold">{profile360Data.data.feedback_summary.difficulty_breakdown.VERY_HARD || 0}</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* Placed Candidates Table */}
              <Card>
                <div className="p-4 border-b border-gqt-neutral-100 flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy flex items-center gap-2">
                    <Award className="w-4 h-4 text-emerald-600" />
                    Placed Candidates ({profile360Data.data.placed_candidates.length})
                  </h4>
                </div>
                {profile360Data.data.placed_candidates.length === 0 ? (
                  <div className="p-6 text-center text-xs text-gqt-neutral-500">
                    No selected candidates recorded for this hiring partner yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-600 uppercase font-bold text-[10px]">
                        <tr>
                          <th className="py-2.5 px-4">Student</th>
                          <th className="py-2.5 px-4">Roll Number</th>
                          <th className="py-2.5 px-4">Drive Title</th>
                          <th className="py-2.5 px-4">Designation</th>
                          <th className="py-2.5 px-4">CTC Offered</th>
                          <th className="py-2.5 px-4">Offer Status</th>
                          <th className="py-2.5 px-4">Joining Status</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gqt-neutral-100">
                        {profile360Data.data.placed_candidates.map((cand) => (
                          <tr key={cand.id} className="hover:bg-gqt-neutral-50/50">
                            <td className="py-2.5 px-4 font-semibold text-gqt-navy">{cand.student_name}</td>
                            <td className="py-2.5 px-4 font-mono text-[11px] text-gqt-neutral-600">{cand.student_roll_number}</td>
                            <td className="py-2.5 px-4 text-gqt-charcoal">{cand.job_title}</td>
                            <td className="py-2.5 px-4 text-gqt-charcoal">{cand.designation_offered}</td>
                            <td className="py-2.5 px-4 font-semibold text-gqt-navy">
                              {cand.offered_ctc ? `₹${cand.offered_ctc.toLocaleString()}` : 'N/A'}
                            </td>
                            <td className="py-2.5 px-4">
                              <StatusBadge
                                variant={cand.acceptance_status === 'ACCEPTED' ? 'success' : 'neutral'}
                                label={cand.acceptance_status}
                              />
                            </td>
                            <td className="py-2.5 px-4">
                              <StatusBadge
                                variant={
                                  cand.joining_status === 'JOINED'
                                    ? 'success'
                                    : cand.joining_status === 'DEFERRED'
                                    ? 'warning'
                                    : cand.joining_status === 'NOT_JOINED'
                                    ? 'danger'
                                    : 'neutral'
                                }
                                label={cand.joining_status}
                              />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>

              {/* Recruitment Drives History */}
              <Card>
                <div className="p-4 border-b border-gqt-neutral-100 flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy flex items-center gap-2">
                    <Briefcase className="w-4 h-4 text-gqt-blue" />
                    Recruitment Drives ({profile360Data.data.recruitment_drives.length})
                  </h4>
                </div>
                {profile360Data.data.recruitment_drives.length === 0 ? (
                  <div className="p-6 text-center text-xs text-gqt-neutral-500">
                    No job drives recorded for this company.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-600 uppercase font-bold text-[10px]">
                        <tr>
                          <th className="py-2.5 px-4">Job Title</th>
                          <th className="py-2.5 px-4">Status</th>
                          <th className="py-2.5 px-4">Openings</th>
                          <th className="py-2.5 px-4">Interview Date</th>
                          <th className="py-2.5 px-4">Selected</th>
                          <th className="py-2.5 px-4">Created</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gqt-neutral-100">
                        {profile360Data.data.recruitment_drives.map((drive) => (
                          <tr key={drive.id} className="hover:bg-gqt-neutral-50/50">
                            <td className="py-2.5 px-4 font-semibold text-gqt-navy">{drive.title}</td>
                            <td className="py-2.5 px-4">
                              <StatusBadge
                                variant={drive.status === 'APPROVED' ? 'success' : 'neutral'}
                                label={drive.status}
                              />
                            </td>
                            <td className="py-2.5 px-4 text-gqt-charcoal">{drive.openings_count}</td>
                            <td className="py-2.5 px-4 text-gqt-neutral-600">
                              {drive.interview_date ? new Date(drive.interview_date).toLocaleDateString() : 'TBD'}
                            </td>
                            <td className="py-2.5 px-4 font-semibold text-emerald-700">{drive.placed_count}</td>
                            <td className="py-2.5 px-4 text-gqt-neutral-400">
                              {new Date(drive.created_at).toLocaleDateString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Card>
            </>
          )}
        </div>
      )}

      {/* Communication Timeline Tab */}
      {activeTab === 'timeline' && (
        <Card className="p-6">
          <div className="flex items-center justify-between pb-4 border-b border-gqt-neutral-100 mb-6">
            <div>
              <h3 className="text-sm font-bold text-gqt-navy flex items-center gap-2">
                <Send className="w-4 h-4 text-gqt-blue" />
                Chronological Communication History
              </h3>
              <p className="text-xs text-gqt-neutral-500 mt-0.5">
                Unified multi-channel timeline combining Outreach calls/emails, candidate profile dispatches, and placement advisories.
              </p>
            </div>
          </div>

          {isTimelineLoading ? (
            <LoadingState message="Assembling multi-channel communication timeline..." />
          ) : !timelineData?.data || timelineData.data.length === 0 ? (
            <div className="p-8 text-center text-xs text-gqt-neutral-500">
              No communication logs recorded for this company across any channel yet.
            </div>
          ) : (
            <div className="relative pl-6 border-l-2 border-gqt-neutral-200 space-y-6">
              {timelineData.data.map((event) => (
                <div key={event.id} className="relative group">
                  {/* Timeline dot */}
                  <div className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-white border-2 border-gqt-blue group-hover:bg-gqt-blue transition-colors" />

                  <div className="p-4 rounded-xl border border-gqt-neutral-200/80 bg-white shadow-sm hover:border-gqt-neutral-300 transition-colors">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-gqt-neutral-100 text-gqt-navy">
                          {event.category.replace(/_/g, ' ')}
                        </span>
                        <span className="text-xs font-semibold text-gqt-neutral-600">
                          via {event.channel_display || event.channel}
                        </span>
                        <StatusBadge
                          variant={event.direction === 'INBOUND' ? 'info' : 'neutral'}
                          label={event.direction}
                          showDot={false}
                        />
                      </div>
                      <span className="text-[11px] font-mono text-gqt-neutral-500">
                        {new Date(event.timestamp).toLocaleString()}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-gqt-navy mt-2">{event.subject}</h4>
                    <p className="text-xs text-gqt-neutral-600 mt-1 whitespace-pre-wrap">{event.summary}</p>

                    <div className="mt-3 pt-2 border-t border-gqt-neutral-100 flex flex-wrap items-center justify-between text-[11px] text-gqt-neutral-500">
                      <span>Logged by: <strong className="text-gqt-charcoal">{event.actor_name || 'System'}</strong></span>
                      {event.contact_name && (
                        <span>HR Contact: <strong className="text-gqt-charcoal">{event.contact_name}</strong></span>
                      )}
                      <span className="uppercase font-semibold text-emerald-600">{event.status}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}
    </div>
  );
};
