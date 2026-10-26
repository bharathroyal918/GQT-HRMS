import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Lock,
  CheckCircle2,
  FileText,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { studentsApi } from '@/api/studentsApi';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const CandidateCohortPage: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [finalizeModalOpen, setFinalizeModalOpen] = useState(false);
  const [finalizationNotes, setFinalizationNotes] = useState('');
  const [finalizeError, setFinalizeError] = useState<string | null>(null);

  // Check if current user has authorization to finalize cohort (Placement Head or Admin only)
  const canFinalize =
    user?.is_superuser ||
    (user?.roles || []).some(r => r === 'PLACEMENT_HEAD' || r === 'ADMIN');

  // Fetch job details
  const {
    data: job,
    isLoading: jobLoading,
    error: jobError,
  } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: !!jobId,
  });

  // Fetch cohort
  const {
    data: cohort,
    isLoading: cohortLoading,
  } = useQuery({
    queryKey: ['cohort-for-job', jobId],
    queryFn: () => studentsApi.getCohort(jobId!),
    enabled: !!jobId,
    retry: 1,
  });

  // Finalize mutation
  const finalizeMutation = useMutation({
    mutationFn: () =>
      studentsApi.finalizeCohort(jobId!, { notes: finalizationNotes }),
    onSuccess: () => {
      setFinalizeModalOpen(false);
      setFinalizationNotes('');
      setFinalizeError(null);
      queryClient.invalidateQueries({ queryKey: ['cohort-for-job', jobId] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Failed to lock cohort.';
      setFinalizeError(msg);
    },
  });

  if (jobLoading) return <LoadingState message="Loading job details..." />;
  if (jobError || !job) return <ErrorState message="Could not load job requirement." />;

  const isLocked = cohort?.is_locked || false;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Top Breadcrumbs */}
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
              Eligibility Engine Workspace
            </Button>
          </Link>
        </div>
      </div>

      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-gqt-neutral-200/80 p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
              Step 14: Candidate Cohort
            </span>
            <StatusBadge
              variant={isLocked ? 'success' : 'warning'}
              label={isLocked ? 'Cohort Finalized & Locked' : 'Cohort Open for Verification'}
            />
          </div>
          <h1 className="text-2xl font-bold text-gqt-navy">
            {cohort?.title || `Candidate Cohort — ${job.title}`}
          </h1>
          <p className="text-sm text-gqt-neutral-500 mt-0.5">
            {job.company_name} &bull; Drive Date:{' '}
            {job.interview_date ? new Date(job.interview_date).toLocaleDateString() : 'To be announced'}
          </p>
        </div>

        <div>
          {!isLocked ? (
            <Button
              onClick={() => setFinalizeModalOpen(true)}
              disabled={!canFinalize}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              <Lock className="w-4 h-4 mr-1.5" />
              Finalize & Lock Cohort
            </Button>
          ) : (
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-lg">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Certified by {cohort?.finalized_by_name || 'Placement Head'}</span>
            </div>
          )}
        </div>
      </div>

      {/* Locked Notice Banner */}
      {isLocked && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200/80 text-emerald-900 flex items-start gap-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-sm">
              Candidate Cohort Locked ({cohort?.eligible_member_count} Certified Candidates)
            </h4>
            <p className="text-xs mt-0.5 text-emerald-800">
              This candidate list was formally locked on{' '}
              {cohort?.finalized_at ? new Date(cohort.finalized_at).toLocaleString() : ''} by{' '}
              {cohort?.finalized_by_name}. Membership is immutable and preserved for downstream Phase 5 candidate packaging and company submission.
            </p>
            {cohort?.finalization_notes && (
              <p className="text-xs italic text-emerald-950 mt-1">
                &ldquo;{cohort.finalization_notes}&rdquo;
              </p>
            )}
          </div>
        </div>
      )}

      {/* Cohort Roster Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Users className="w-5 h-5 text-gqt-blue" />
                Verified Candidate Roster
              </CardTitle>
              <CardDescription>
                Eligible students qualified via automated rule evaluation or authorized placement officer overrides.
              </CardDescription>
            </div>
            <div className="text-xs font-medium text-gqt-neutral-500">
              Verified Members: <span className="font-bold text-gqt-navy">{cohort?.members?.length || 0}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {cohortLoading ? (
            <LoadingState message="Loading candidate cohort..." />
          ) : !cohort || !cohort.members || cohort.members.length === 0 ? (
            <div className="text-center py-10 space-y-3">
              <p className="text-sm text-gqt-neutral-500">
                The candidate cohort has not been compiled or finalized yet.
              </p>
              {canFinalize && !isLocked && (
                <Button size="sm" onClick={() => setFinalizeModalOpen(true)}>
                  Compile & Lock Cohort Now
                </Button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gqt-neutral-200 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <th className="pb-3">Roll Number</th>
                    <th className="pb-3">Student Name</th>
                    <th className="pb-3">Discipline</th>
                    <th className="pb-3">CGPA</th>
                    <th className="pb-3">Backlogs</th>
                    <th className="pb-3">Resume</th>
                    <th className="pb-3">Qualification Mode</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {cohort.members.map(m => (
                    <tr key={m.id} className="hover:bg-gqt-neutral-50/50">
                      <td className="py-3 font-mono text-xs font-bold text-gqt-navy">{m.student_roll}</td>
                      <td className="py-3">
                        <span className="font-medium text-gqt-navy block">{m.student_name}</span>
                        <span className="text-xs text-gqt-neutral-400">{m.student_email}</span>
                      </td>
                      <td className="py-3 text-gqt-neutral-600">{m.student_department}</td>
                      <td className="py-3 font-semibold text-gqt-navy">{m.student_cgpa}</td>
                      <td className="py-3">
                        <span
                          className={m.student_active_backlogs > 0 ? 'text-amber-600 font-semibold' : 'text-emerald-600'}
                        >
                          {m.student_active_backlogs}
                        </span>
                      </td>
                      <td className="py-3">
                        {m.resume_id ? (
                          <a
                            href={studentsApi.getResumeDownloadUrl(m.resume_id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-xs font-medium text-gqt-blue hover:underline"
                          >
                            <FileText className="w-3.5 h-3.5 mr-1" />
                            v{m.resume_version}
                          </a>
                        ) : (
                          <span className="text-xs text-gqt-neutral-400">None</span>
                        )}
                      </td>
                      <td className="py-3">
                        {m.is_override ? (
                          <div className="flex flex-col items-start">
                            <span className="inline-flex items-center text-[11px] font-semibold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full">
                              Manual Override
                            </span>
                            <span className="text-[10px] text-gqt-neutral-400 mt-0.5 truncate max-w-[200px]" title={m.override_reason}>
                              {m.override_reason}
                            </span>
                          </div>
                        ) : (
                          <span className="inline-flex items-center text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                            <CheckCircle2 className="w-3 h-3 mr-1" /> Automated Engine
                          </span>
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

      {/* Finalize Modal */}
      {finalizeModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                <Lock className="w-5 h-5 text-emerald-600" />
                Finalize & Lock Candidate Cohort
              </h3>
              <button
                onClick={() => setFinalizeModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-neutral-600"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-gqt-neutral-500">
              Workflow Step 14: You are about to certify and formally lock the verified candidate cohort for{' '}
              <span className="font-semibold text-gqt-navy">{job.title}</span>. Locking freezes the candidate list to guarantee integrity for downstream candidate rosters and company submissions.
            </p>

            {finalizeError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-md">
                {finalizeError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                Operational Notes / Drive Instructions (Optional)
              </label>
              <textarea
                rows={3}
                value={finalizationNotes}
                onChange={e => setFinalizationNotes(e.target.value)}
                className="w-full rounded-md border border-gqt-neutral-300 p-2.5 text-sm"
                placeholder="e.g. Certified 42 eligible circuit branch candidates for Cognizant drive on 15-Nov..."
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setFinalizeModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700"
                onClick={() => finalizeMutation.mutate()}
                disabled={finalizeMutation.isPending}
              >
                {finalizeMutation.isPending ? 'Finalizing...' : 'Certify & Lock Cohort'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
