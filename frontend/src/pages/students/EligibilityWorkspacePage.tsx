import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  FileText,
  ShieldAlert,
  Edit3,
  Users,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { studentsApi } from '@/api/studentsApi';
import { EligibilityEvaluation } from '@/types/students';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const EligibilityWorkspacePage: React.FC = () => {
  const { id: jobId } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [selectedEvaluation, setSelectedEvaluation] = useState<EligibilityEvaluation | null>(null);
  const [overrideModalOpen, setOverrideModalOpen] = useState(false);
  const [overrideEvalId, setOverrideEvalId] = useState<string>('');
  const [overrideIsEligible, setOverrideIsEligible] = useState<boolean>(true);
  const [overrideReason, setOverrideReason] = useState<string>('');
  const [overrideError, setOverrideError] = useState<string | null>(null);

  // Fetch job requirement
  const {
    data: job,
    isLoading: jobLoading,
    error: jobError,
  } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJob(jobId!),
    enabled: !!jobId,
  });

  // Fetch applications for this job
  const {
    data: applications,
    isLoading: appsLoading,
  } = useQuery({
    queryKey: ['applications-for-job', jobId],
    queryFn: () => studentsApi.listApplications({ job_id: jobId }),
    enabled: !!jobId,
  });

  // Override mutation
  const overrideMutation = useMutation({
    mutationFn: () =>
      studentsApi.overrideEligibility(overrideEvalId, {
        is_eligible: overrideIsEligible,
        override_reason: overrideReason,
      }),
    onSuccess: () => {
      setOverrideModalOpen(false);
      setOverrideReason('');
      setOverrideError(null);
      queryClient.invalidateQueries({ queryKey: ['applications-for-job', jobId] });
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || err.message || 'Override failed.';
      setOverrideError(msg);
    },
  });

  const openOverrideDialog = (evalId: string, currentStatus: string) => {
    setOverrideEvalId(evalId);
    setOverrideIsEligible(currentStatus !== 'ELIGIBLE');
    setOverrideReason('');
    setOverrideError(null);
    setOverrideModalOpen(true);
  };

  if (jobLoading) return <LoadingState message="Loading job requirement criteria..." />;
  if (jobError || !job) return <ErrorState message="Could not load job requirement." />;

  const getStatusVariant = (st: string): StatusVariant => {
    switch (st) {
      case 'ELIGIBLE':
        return 'success';
      case 'OVERRIDDEN':
        return 'info';
      case 'INELIGIBLE':
        return 'danger';
      default:
        return 'warning';
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <Link
          to={`/jobs/${job.id}`}
          className="inline-flex items-center text-sm font-medium text-gqt-neutral-500 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1.5" />
          Back to Job Details
        </Link>
        <div className="flex items-center gap-2">
          <Link to={`/jobs/${job.id}/publish`}>
            <Button variant="outline" size="sm">
              Publication Notices
            </Button>
          </Link>
          <Link to={`/jobs/${job.id}/cohort`}>
            <Button variant="outline" size="sm">
              <Users className="w-4 h-4 mr-1.5" />
              Candidate Cohort
            </Button>
          </Link>
        </div>
      </div>

      {/* Header Banner & Job Criteria */}
      <div className="bg-white rounded-xl border border-gqt-neutral-200/80 p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
                Step 13: Eligibility Engine
              </span>
              <StatusBadge
                variant={job.status === 'APPROVED' ? 'success' : 'neutral'}
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

        {/* Established Criteria Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-4 border-t border-gqt-neutral-100">
          <div className="p-3 bg-gqt-neutral-50 rounded-lg text-xs">
            <span className="text-gqt-neutral-400 font-medium uppercase block">Min Academic CGPA</span>
            <span className="text-sm font-bold text-gqt-navy mt-0.5 block">
              {job.min_cgpa ? `>= ${job.min_cgpa}` : 'No minimum'}
            </span>
          </div>
          <div className="p-3 bg-gqt-neutral-50 rounded-lg text-xs">
            <span className="text-gqt-neutral-400 font-medium uppercase block">Standing Arrears Limit</span>
            <span className="text-sm font-bold text-gqt-navy mt-0.5 block">
              0 Active Backlogs
            </span>
          </div>
          <div className="p-3 bg-gqt-neutral-50 rounded-lg text-xs">
            <span className="text-gqt-neutral-400 font-medium uppercase block">Permitted Disciplines</span>
            <span className="text-sm font-bold text-gqt-navy mt-0.5 block truncate">
              Specified in JD Criteria
            </span>
          </div>
          <div className="p-3 bg-gqt-neutral-50 rounded-lg text-xs">
            <span className="text-gqt-neutral-400 font-medium uppercase block">Target Batch</span>
            <span className="text-sm font-bold text-gqt-navy mt-0.5 block">
              {job.interview_date ? new Date(job.interview_date).getFullYear() : '2025'} Passing
            </span>
          </div>
        </div>
      </div>

      {/* Applications Directory & Evaluation Table */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle className="text-base">Registered Applicants & Rule Engine Evaluations</CardTitle>
              <CardDescription>
                Auditable evaluation results with criterion-level explanations and authorized manual overrides.
              </CardDescription>
            </div>
            <div className="text-xs font-medium text-gqt-neutral-500">
              Total Applicants: <span className="font-bold text-gqt-navy">{applications?.length || 0}</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {appsLoading ? (
            <LoadingState message="Evaluating candidate applications..." />
          ) : !applications || applications.length === 0 ? (
            <p className="text-sm text-gqt-neutral-500 py-8 text-center">
              No students have applied for this opportunity yet.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gqt-neutral-200 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <th className="pb-3">Candidate</th>
                    <th className="pb-3">Department</th>
                    <th className="pb-3">CGPA</th>
                    <th className="pb-3">Backlogs</th>
                    <th className="pb-3">Resume</th>
                    <th className="pb-3">Status</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {applications.map(app => {
                    const ev = app.eligibility_evaluation;
                    return (
                      <tr key={app.id} className="hover:bg-gqt-neutral-50/50">
                        <td className="py-3">
                          <span className="font-semibold text-gqt-navy block">{app.student_name}</span>
                          <span className="text-xs font-mono text-gqt-neutral-400">{app.student_roll}</span>
                        </td>
                        <td className="py-3 text-gqt-neutral-600">{app.student_department}</td>
                        <td className="py-3 font-semibold text-gqt-navy">{app.student_cgpa}</td>
                        <td className="py-3">
                          <span
                            className={app.student_active_backlogs > 0 ? 'text-amber-600 font-semibold' : 'text-emerald-600'}
                          >
                            {app.student_active_backlogs}
                          </span>
                        </td>
                        <td className="py-3">
                          {app.resume_id ? (
                            <a
                              href={studentsApi.getResumeDownloadUrl(app.resume_id)}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center text-xs font-medium text-gqt-blue hover:underline"
                            >
                              <FileText className="w-3.5 h-3.5 mr-1" />
                              v{app.resume_version}
                            </a>
                          ) : (
                            <span className="text-xs text-gqt-neutral-400">None</span>
                          )}
                        </td>
                        <td className="py-3">
                          <div className="flex flex-col items-start gap-1">
                            <StatusBadge
                              variant={getStatusVariant(app.status)}
                              label={app.status_display}
                            />
                            {ev?.is_overridden && (
                              <span className="text-[10px] text-amber-700 font-medium">
                                Override by {ev.override_by_name || 'Staff'}
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3 text-right space-x-2">
                          {ev && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => setSelectedEvaluation(ev)}
                            >
                              Inspect Details
                            </Button>
                          )}
                          {ev && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => openOverrideDialog(ev.id, ev.status)}
                            >
                              <Edit3 className="w-3.5 h-3.5 mr-1" />
                              Override
                            </Button>
                          )}
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

      {/* Evaluation Explanation Drawer / Card */}
      {selectedEvaluation && (
        <Card className="border-gqt-blue/40 shadow-md">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-gqt-blue" />
                Criterion-by-Criterion Evaluation Breakdown
              </CardTitle>
              <CardDescription>
                Auditable evaluation result recorded by the Step 13 Eligibility Verification Engine.
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={() => setSelectedEvaluation(null)}>
              Close Breakdown
            </Button>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {(selectedEvaluation.evaluation_details || []).map((crit, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-lg border text-sm ${
                    crit.passed ? 'bg-emerald-50/40 border-emerald-200' : 'bg-rose-50/40 border-rose-200'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gqt-navy">{crit.criterion}</span>
                    {crit.passed ? (
                      <span className="inline-flex items-center text-xs font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center text-xs font-semibold text-rose-700 bg-rose-100 px-2 py-0.5 rounded-full">
                        <XCircle className="w-3 h-3 mr-1" /> Failed
                      </span>
                    )}
                  </div>
                  <div className="text-xs space-y-1 text-gqt-neutral-600">
                    <div>
                      <span className="font-medium text-gqt-neutral-400">Required: </span>
                      {crit.required_value}
                    </div>
                    <div>
                      <span className="font-medium text-gqt-neutral-400">Actual Value: </span>
                      <span className="font-semibold">{crit.student_value}</span>
                    </div>
                    <p className="mt-2 text-xs italic text-gqt-neutral-700">{crit.details}</p>
                  </div>
                </div>
              ))}
            </div>

            {selectedEvaluation.is_overridden && (
              <div className="p-4 rounded-lg bg-amber-50 border border-amber-200 text-sm">
                <span className="font-semibold text-amber-800 flex items-center gap-1.5 mb-1">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  Manual Placement Override Record
                </span>
                <p className="text-xs text-amber-900">
                  <span className="font-medium">Authorized by:</span>{' '}
                  {selectedEvaluation.override_by_name || 'Placement Officer'}&bull;{' '}
                  {selectedEvaluation.override_at ? new Date(selectedEvaluation.override_at).toLocaleString() : ''}
                </p>
                <p className="text-xs text-amber-950 mt-1">
                  <span className="font-medium">Business Reason:</span> {selectedEvaluation.override_reason}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Manual Override Modal */}
      {overrideModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-gqt-navy flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-amber-600" />
                Authorize Eligibility Override
              </h3>
              <button
                onClick={() => setOverrideModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-neutral-600"
              >
                &times;
              </button>
            </div>

            <p className="text-xs text-gqt-neutral-500">
              Workflow Step 14: Placement Officers and Heads may manually override automated rule evaluation outcomes. Every override is immutably recorded in the security audit trail.
            </p>

            {overrideError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-md">
                {overrideError}
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Target Qualification Decision
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center text-sm font-medium text-gqt-neutral-700">
                    <input
                      type="radio"
                      checked={overrideIsEligible === true}
                      onChange={() => setOverrideIsEligible(true)}
                      className="mr-1.5"
                    />
                    Grant Candidate Eligibility
                  </label>
                  <label className="flex items-center text-sm font-medium text-gqt-neutral-700">
                    <input
                      type="radio"
                      checked={overrideIsEligible === false}
                      onChange={() => setOverrideIsEligible(false)}
                      className="mr-1.5"
                    />
                    Mark Candidate Ineligible
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gqt-neutral-600 uppercase mb-1">
                  Mandatory Business Justification <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={3}
                  value={overrideReason}
                  onChange={e => setOverrideReason(e.target.value)}
                  className="w-full rounded-md border border-gqt-neutral-300 p-2.5 text-sm"
                  placeholder="Provide explicit operational rationale for overriding automated criteria (min 10 characters)..."
                />
                <span className="text-[11px] text-gqt-neutral-400">
                  Minimum 10 characters required for audit attribution.
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={() => setOverrideModalOpen(false)}>
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={() => overrideMutation.mutate()}
                disabled={overrideMutation.isPending || overrideReason.trim().length < 10}
              >
                {overrideMutation.isPending ? 'Recording Override...' : 'Confirm Override'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
