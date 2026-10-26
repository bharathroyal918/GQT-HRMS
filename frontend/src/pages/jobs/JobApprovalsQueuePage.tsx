import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, Link } from 'react-router-dom';
import {
  FileCheck,
  CheckCircle2,
  Clock,
  ArrowLeft,
  Building2,
  Eye,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { JobRequirementListItem } from '@/types/jobs';
import { Button } from '@/components/common/Button';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

export const JobApprovalsQueuePage: React.FC = () => {
  const navigate = useNavigate();
  const [activeQueue, setActiveQueue] = useState<'verification' | 'signoff'>('verification');

  const {
    data: verificationQueue,
    isLoading: isLoadingVerification,
    isError: isErrorVerification,
    refetch: refetchVerification,
  } = useQuery({
    queryKey: ['queue-verification'],
    queryFn: () => jobsApi.getPendingVerification(),
  });

  const {
    data: signoffQueue,
    isLoading: isLoadingSignoff,
    isError: isErrorSignoff,
    refetch: refetchSignoff,
  } = useQuery({
    queryKey: ['queue-signoff'],
    queryFn: () => jobsApi.getPendingApproval(),
  });

  const formatDeadline = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  const formatSalary = (min: string | null, max: string | null, currency: string) => {
    if (!min && !max) return 'Not Disclosed';
    const curr = currency === 'INR' ? '₹' : currency;
    if (min && max) {
      const minLPA = (parseFloat(min) / 100000).toFixed(1);
      const maxLPA = (parseFloat(max) / 100000).toFixed(1);
      return `${curr}${minLPA} - ${maxLPA} LPA`;
    }
    if (min) return `${curr}${(parseFloat(min) / 100000).toFixed(1)} LPA+`;
    return `Up to ${curr}${(parseFloat(max!) / 100000).toFixed(1)} LPA`;
  };

  const currentList =
    activeQueue === 'verification' ? verificationQueue?.data : signoffQueue?.data;
  const isLoading =
    activeQueue === 'verification' ? isLoadingVerification : isLoadingSignoff;
  const isError = activeQueue === 'verification' ? isErrorVerification : isErrorSignoff;
  const refetch = activeQueue === 'verification' ? refetchVerification : refetchSignoff;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Navigation Header */}
      <div className="flex items-center justify-between">
        <Link
          to="/jobs"
          className="inline-flex items-center gap-1.5 text-sm font-medium text-gqt-neutral-600 hover:text-gqt-navy transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Requirements Directory
        </Link>
        <span className="text-xs text-gqt-neutral-500 font-mono">
          Workflow Steps 6 & 7: Operational Queues
        </span>
      </div>

      <div>
        <h1 className="text-2xl font-bold text-gqt-navy flex items-center gap-2">
          <FileCheck className="w-7 h-7 text-gqt-blue" />
          Review & Approval Workspace
        </h1>
        <p className="text-sm text-gqt-neutral-600 mt-1">
          Dedicated operational queues for Placement Officers conducting 5-point checklist audits and Placement Heads executing formal opportunity approvals.
        </p>
      </div>

      {/* Queue Switcher Tabs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <button
          onClick={() => setActiveQueue('verification')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeQueue === 'verification'
              ? 'bg-blue-50/70 border-gqt-blue shadow-sm'
              : 'bg-white border-gqt-neutral-200 hover:border-gqt-neutral-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1.5">
              <Clock className="w-4 h-4" /> Step 6: Checklist Audit Queue
            </span>
            <span className="text-sm font-bold px-2 py-0.5 rounded-full bg-white text-gqt-navy border border-gqt-neutral-200">
              {verificationQueue?.meta?.count || 0}
            </span>
          </div>
          <h3 className="text-lg font-bold text-gqt-navy mt-2">Pending Checklist Verification</h3>
          <p className="text-xs text-gqt-neutral-600 mt-1">
            Jobs submitted by corporate intake staff awaiting verification of Eligibility, Salary, Company Authenticity, Interview Process, and Deadlines.
          </p>
        </button>

        <button
          onClick={() => setActiveQueue('signoff')}
          className={`p-4 rounded-xl border text-left transition-all ${
            activeQueue === 'signoff'
              ? 'bg-emerald-50/70 border-emerald-500 shadow-sm'
              : 'bg-white border-gqt-neutral-200 hover:border-gqt-neutral-300'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Step 7: Head Approval Queue
            </span>
            <span className="text-sm font-bold px-2 py-0.5 rounded-full bg-white text-gqt-navy border border-gqt-neutral-200">
              {signoffQueue?.meta?.count || 0}
            </span>
          </div>
          <h3 className="text-lg font-bold text-gqt-navy mt-2">Awaiting Placement Head Sign-Off</h3>
          <p className="text-xs text-gqt-neutral-600 mt-1">
            Opportunities where all 5 mandatory criteria evaluate to 100% verified, pending executive sign-off to lock for Phase 4 design creatives.
          </p>
        </button>
      </div>

      {/* Queue Content */}
      {isLoading ? (
        <LoadingState message="Loading review queue..." />
      ) : isError ? (
        <ErrorState
          title="Error Loading Queue"
          message="Could not load the specified queue."
          onRetry={refetch}
        />
      ) : !currentList || currentList.length === 0 ? (
        <EmptyState
          title={
            activeQueue === 'verification'
              ? 'Checklist Verification Queue Clean'
              : 'Approval Queue Clean'
          }
          description={
            activeQueue === 'verification'
              ? 'No job requirements are currently waiting for 5-point checklist verification.'
              : 'No verified opportunities are currently waiting for Placement Head sign-off.'
          }
          action={
            <Button variant="outline" size="sm" onClick={() => navigate('/jobs')}>
              View All Requirements
            </Button>
          }
        />
      ) : (
        <div className="bg-white rounded-xl shadow-card border border-gqt-neutral-200/80 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gqt-neutral-50 text-gqt-neutral-600 font-semibold border-b border-gqt-neutral-200 uppercase text-xs tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Role Title & Company</th>
                <th className="py-3.5 px-4">Location</th>
                <th className="py-3.5 px-4">Compensation</th>
                <th className="py-3.5 px-4">5-Point Checklist</th>
                <th className="py-3.5 px-4">Registration Deadline</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gqt-neutral-200/70">
              {currentList.map((job: JobRequirementListItem) => {
                const progress = job.checklist_progress;

                return (
                  <tr
                    key={job.id}
                    className="hover:bg-blue-50/40 transition-colors cursor-pointer"
                    onClick={() => navigate(`/jobs/${job.id}`)}
                  >
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-gqt-navy hover:text-gqt-blue">
                        {job.title}
                      </div>
                      <div className="text-xs text-gqt-neutral-500 mt-0.5 flex items-center gap-1">
                        <Building2 className="w-3.5 h-3.5" />
                        <span>{job.company_name}</span>
                        <span>•</span>
                        <span>{job.openings_count} openings</span>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-gqt-neutral-800">
                      {job.location}
                    </td>

                    <td className="py-3.5 px-4 font-semibold text-gqt-navy">
                      {formatSalary(job.min_salary, job.max_salary, job.salary_currency)}
                    </td>

                    <td className="py-3.5 px-4">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium text-gqt-neutral-700">
                            {progress?.verified_mandatory || 0}/{progress?.total_mandatory || 5} Points
                          </span>
                          <span className="text-gqt-neutral-400">{progress?.percentage || 0}%</span>
                        </div>
                        <div className="w-28 bg-gqt-neutral-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              progress?.is_complete ? 'bg-emerald-500' : 'bg-amber-500'
                            }`}
                            style={{ width: `${progress?.percentage || 0}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-xs font-semibold text-rose-600">
                      {formatDeadline(job.registration_deadline)}
                    </td>

                    <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                      <Button
                        size="sm"
                        variant={activeQueue === 'signoff' ? 'primary' : 'outline'}
                        className={activeQueue === 'signoff' ? 'bg-emerald-600 hover:bg-emerald-700' : ''}
                        onClick={() => navigate(`/jobs/${job.id}`)}
                        leftIcon={
                          activeQueue === 'signoff' ? (
                            <CheckCircle2 className="w-3.5 h-3.5" />
                          ) : (
                            <Eye className="w-3.5 h-3.5" />
                          )
                        }
                      >
                        {activeQueue === 'signoff' ? 'Review & Sign' : 'Audit Checklist'}
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
