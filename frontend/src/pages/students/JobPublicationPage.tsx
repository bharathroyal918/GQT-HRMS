import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Send, RotateCw, AlertTriangle, CheckCircle, ShieldCheck, Megaphone, Smartphone, Mail, Globe, MessageSquare } from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { creativesApi } from '@/api/creativesApi';
import { studentsApi } from '@/api/studentsApi';
import { JobPublicationChannel, JobPublicationStatus } from '@/types/students';
import { CreativeRequestListItem } from '@/types/creatives';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const JobPublicationPage: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [channel, setChannel] = useState<JobPublicationChannel>('WHATSAPP');
  const [targetAudience, setTargetAudience] = useState('2025 Passing Out Batch — Circuit Branches (CS, IS, EC)');
  const [selectedCreativeId, setSelectedCreativeId] = useState<string>('');
  const [customSubject, setCustomSubject] = useState('');
  const [customBody, setCustomBody] = useState('');
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch approved job requirement
  const {
    data: job,
    isLoading: jobLoading,
    error: jobError,
  } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: !!jobId,
  });

  // Fetch creatives for this job to link approved assets
  const { data: creativeRequests } = useQuery({
    queryKey: ['creatives-for-job', jobId],
    queryFn: () => creativesApi.getCreativeRequests({ job_requirement: jobId }),
    enabled: !!jobId,
  });

  // Fetch publication history
  const {
    data: publications,
    isLoading: pubLoading,
  } = useQuery({
    queryKey: ['publications', jobId],
    queryFn: () => studentsApi.listPublications(jobId!),
    enabled: !!jobId,
  });

  // Publish mutation
  const publishMutation = useMutation({
    mutationFn: () =>
      studentsApi.createPublication({
        job_requirement_id: jobId!,
        channel,
        target_audience: targetAudience,
        creative_version_id: selectedCreativeId || null,
        subject: customSubject || undefined,
        message_body: customBody || undefined,
      }),
    onSuccess: () => {
      setSuccessMessage('Job announcement broadcasted successfully.');
      setFormError(null);
      queryClient.invalidateQueries({ queryKey: ['publications', jobId] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to dispatch publication.';
      setFormError(msg);
      setSuccessMessage(null);
    },
  });

  // Retry mutation
  const retryMutation = useMutation({
    mutationFn: (pubId: string) => studentsApi.retryPublication(pubId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['publications', jobId] });
    },
  });

  if (jobLoading) return <LoadingState message="Loading job requirement details..." />;
  if (jobError || !job) return <ErrorState message="Could not load job requirement." />;

  const isApproved = job.status === 'APPROVED';

  // Find approved creative deliverables for this job
  const approvedCreativeRequests = (creativeRequests?.data || []).filter(
    (req: CreativeRequestListItem) => req.status === 'APPROVED'
  );

  const getStatusVariant = (st: JobPublicationStatus): StatusVariant => {
    switch (st) {
      case 'DELIVERED':
        return 'success';
      case 'DISPATCHED':
      case 'QUEUED':
        return 'info';
      case 'FAILED':
        return 'danger';
      case 'CANCELLED':
        return 'neutral';
      default:
        return 'warning';
    }
  };

  const getChannelIcon = (ch: JobPublicationChannel) => {
    switch (ch) {
      case 'WHATSAPP':
        return <Smartphone className="w-4 h-4 text-emerald-600" />;
      case 'TELEGRAM':
        return <MessageSquare className="w-4 h-4 text-sky-600" />;
      case 'EMAIL':
        return <Mail className="w-4 h-4 text-indigo-600" />;
      case 'PORTAL':
        return <Globe className="w-4 h-4 text-gqt-blue" />;
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Breadcrumb & Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={`/jobs/${job.id}`}
          className="inline-flex items-center text-sm font-medium text-gqt-neutral-500 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back to Job Details
        </Link>
        <div className="flex items-center gap-2">
          <Link to={`/jobs/${job.id}/eligibility`}>
            <Button variant="outline" size="sm">
              Review Applicants & Eligibility
            </Button>
          </Link>
          <Link to={`/jobs/${job.id}/cohort`}>
            <Button variant="outline" size="sm">
              Candidate Cohort
            </Button>
          </Link>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-gqt-neutral-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
              Step 10: Notification Broadcast
            </span>
            <StatusBadge
              variant={isApproved ? 'success' : 'warning'}
              label={job.status}
            />
          </div>
          <h1 className="text-2xl font-bold text-gqt-navy">{job.title}</h1>
          <p className="text-sm text-gqt-neutral-500 mt-0.5">
            {job.company_name || 'Corporate Opportunity'} &bull; {job.location} &bull; Deadline:{' '}
            {new Date(job.registration_deadline).toLocaleDateString()}
          </p>
        </div>
      </div>

      {!isApproved && (
        <div className="p-4 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-800 flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">Publication Gated: Step 7 Approval Required</h4>
            <p className="text-sm mt-0.5">
              According to the authoritative GQT HRMS workflow, only jobs that have completed the 5-point verification checklist and received formal sign-off from the Placement Head can be broadcast to students.
            </p>
          </div>
        </div>
      )}

      {/* Broadcast Form Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Megaphone className="w-5 h-5 text-gqt-blue" />
                Dispatch New Placement Notification
              </CardTitle>
              <CardDescription>
                Publish verified opportunity details to authorized student notification channels.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {formError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700 text-sm">
                  {formError}
                </div>
              )}
              {successMessage && (
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-sm flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600" />
                  {successMessage}
                </div>
              )}

              {/* Channel Selector */}
              <div>
                <label className="block text-sm font-medium text-gqt-neutral-700 mb-1.5">
                  Notification Channel <span className="text-rose-500">*</span>
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  {[
                    { key: 'WHATSAPP', label: 'WhatsApp', icon: Smartphone },
                    { key: 'TELEGRAM', label: 'Telegram', icon: MessageSquare },
                    { key: 'EMAIL', label: 'Email', icon: Mail },
                    { key: 'PORTAL', label: 'Portal', icon: Globe },
                  ].map(ch => {
                    const Icon = ch.icon;
                    const isSelected = channel === ch.key;
                    return (
                      <button
                        key={ch.key}
                        type="button"
                        onClick={() => setChannel(ch.key as JobPublicationChannel)}
                        className={`flex flex-col items-center justify-center p-3 rounded-lg border text-sm font-medium transition-all ${
                          isSelected
                            ? 'border-gqt-blue bg-blue-50/50 text-gqt-navy shadow-xs ring-1 ring-gqt-blue'
                            : 'border-gqt-neutral-200 hover:border-gqt-neutral-300 text-gqt-neutral-600'
                        }`}
                      >
                        <Icon className={`w-5 h-5 mb-1.5 ${isSelected ? 'text-gqt-blue' : 'text-gqt-neutral-400'}`} />
                        {ch.label}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Target Audience */}
              <div>
                <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                  Target Student Cohort <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={targetAudience}
                  onChange={e => setTargetAudience(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  placeholder="e.g. 2025 Passing Out Batch - Circuit Branches"
                />
              </div>

              {/* Link Creative Asset */}
              <div>
                <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                  Attach Approved Promotional Asset (Optional)
                </label>
                <select
                  value={selectedCreativeId}
                  onChange={e => setSelectedCreativeId(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                >
                  <option value="">No creative asset attached (Plain text announcement)</option>
                  {approvedCreativeRequests.map((req: CreativeRequestListItem) => (
                    <option key={req.id} value={req.id}>
                      {req.title} ({req.deliverable_type_display} &bull; Step 9 Certified)
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Only promotional assets with confirmed Step 9 sign-off by the Placement Head can be attached.
                </p>
              </div>

              {/* Headline */}
              <div>
                <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                  Custom Headline / Subject Line (Optional)
                </label>
                <input
                  type="text"
                  value={customSubject}
                  onChange={e => setCustomSubject(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  placeholder={`Campus Drive Notice: ${job.title} at ${job.company_name}`}
                />
              </div>

              {/* Message Body */}
              <div>
                <label className="block text-sm font-medium text-gqt-neutral-700 mb-1">
                  Announcement Message Content (Optional)
                </label>
                <textarea
                  rows={4}
                  value={customBody}
                  onChange={e => setCustomBody(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
                  placeholder="Leave blank to automatically compose a standardized GQT placement announcement."
                />
              </div>

              <div className="pt-2">
                <Button
                  onClick={() => publishMutation.mutate()}
                  disabled={!isApproved || publishMutation.isPending || !targetAudience.trim()}
                  className="w-full sm:w-auto"
                >
                  <Send className="w-4 h-4 mr-2" />
                  {publishMutation.isPending ? 'Broadcasting Notice...' : 'Dispatch Notification Broadcast'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Verification Summary Side Panel */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-gqt-neutral-500">
                Gatekeeper Safeguards
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-xs text-gqt-neutral-600">
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>Only approved jobs with 5 verified checklist points can be published.</span>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>Multi-channel broadcast tracking logs provider message receipts.</span>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>External dispatches never fabricate delivery until confirmed.</span>
              </div>
              <div className="flex items-start gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span>Failed transmissions support manual retry without duplicate alerts.</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Broadcast History Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Broadcast History & Gateway Logs</CardTitle>
          <CardDescription>
            Chronological audit of all notification dispatches across student channels for this opportunity.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {pubLoading ? (
            <LoadingState message="Loading transmission records..." />
          ) : !publications || publications.length === 0 ? (
            <p className="text-sm text-gqt-neutral-500 py-6 text-center">
              No notifications have been broadcasted for this job opportunity yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gqt-neutral-200 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <th className="pb-3">Channel</th>
                    <th className="pb-3">Target Cohort</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3">Dispatched At</th>
                    <th className="pb-3">Gateway Ref</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {publications.map(pub => (
                    <tr key={pub.id} className="hover:bg-gqt-neutral-50/50">
                      <td className="py-3 font-medium flex items-center gap-2">
                        {getChannelIcon(pub.channel)}
                        {pub.channel_display}
                      </td>
                      <td className="py-3 text-gqt-neutral-700">{pub.target_audience}</td>
                      <td className="py-3">
                        <StatusBadge
                          variant={getStatusVariant(pub.status)}
                          label={pub.status_display}
                        />
                      </td>
                      <td className="py-3 text-gqt-neutral-500">
                        {pub.dispatched_at ? new Date(pub.dispatched_at).toLocaleString() : '—'}
                      </td>
                      <td className="py-3 font-mono text-xs text-gqt-neutral-500">
                        {pub.provider_message_id || '—'}
                      </td>
                      <td className="py-3 text-right">
                        {pub.status === 'FAILED' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => retryMutation.mutate(pub.id)}
                            disabled={retryMutation.isPending}
                          >
                            <RotateCw className="w-3.5 h-3.5 mr-1" />
                            Retry
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
