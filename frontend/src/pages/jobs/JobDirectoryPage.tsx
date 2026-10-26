import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Plus,
  Search,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileCheck,
  ChevronRight,
  Eye,
  Edit,
} from 'lucide-react';
import { jobsApi } from '@/api/jobsApi';
import { JobRequirementListItem, JobRequirementStatus } from '@/types/jobs';
import { Button } from '@/components/common/Button';
import { Card, CardContent } from '@/components/common/Card';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';
import { useAuth } from '@/context/AuthContext';

export const JobDirectoryPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [page, setPage] = useState(1);

  const canCreate = user?.roles.some((r) =>
    ['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER'].includes(r)
  );

  const {
    data: jobsData,
    isLoading,
    isError,
    refetch,
  } = useQuery({
    queryKey: ['jobs', { search, statusFilter, typeFilter, page }],
    queryFn: () =>
      jobsApi.getJobs({
        search: search || undefined,
        status: statusFilter || undefined,
        employment_type: typeFilter || undefined,
        page,
      }),
  });

  const { data: metrics } = useQuery({
    queryKey: ['job-metrics'],
    queryFn: () => jobsApi.getJobMetrics(),
  });

  const getStatusBadgeVariant = (status: JobRequirementStatus): StatusVariant => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'VERIFIED':
        return 'info';
      case 'UNDER_REVIEW':
        return 'warning';
      case 'PENDING_VERIFICATION':
        return 'info';
      case 'CHANGES_REQUESTED':
        return 'danger';
      case 'REJECTED':
        return 'danger';
      default:
        return 'neutral';
    }
  };

  const getStatusLabel = (status: JobRequirementStatus): string => {
    switch (status) {
      case 'DRAFT':
        return 'Draft';
      case 'PENDING_VERIFICATION':
        return 'Pending Verification';
      case 'UNDER_REVIEW':
        return 'Under Review';
      case 'CHANGES_REQUESTED':
        return 'Changes Requested';
      case 'VERIFIED':
        return 'Verified';
      case 'APPROVED':
        return 'Approved';
      case 'REJECTED':
        return 'Rejected';
      default:
        return status;
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gqt-navy flex items-center gap-2">
            <Briefcase className="w-7 h-7 text-gqt-blue" />
            Job Requirements & Verification
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Corporate job intake (Step 5), 5-point institutional verification checklist (Step 6), and Placement Head sign-offs (Step 7).
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => navigate('/jobs/approvals')}
            leftIcon={<FileCheck className="w-4 h-4 text-gqt-blue" />}
          >
            Review & Approvals Queue
          </Button>
          {canCreate && (
            <Button
              variant="primary"
              onClick={() => navigate('/jobs/new')}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              New Job Requirement
            </Button>
          )}
        </div>
      </div>

      {/* Metric KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gqt-neutral-500 uppercase">Active Opportunities</p>
              <h3 className="text-2xl font-bold text-gqt-navy mt-1">
                {metrics ? metrics.total_active : '-'}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center text-gqt-blue">
              <Briefcase className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gqt-neutral-500 uppercase">Pending Verification</p>
              <h3 className="text-2xl font-bold text-amber-600 mt-1">
                {metrics ? metrics.pending_verification_count + metrics.under_review_count : '-'}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-amber-50 flex items-center justify-center text-amber-600">
              <Clock className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gqt-neutral-500 uppercase">Awaiting Head Sign-off</p>
              <h3 className="text-2xl font-bold text-indigo-600 mt-1">
                {metrics ? metrics.verified_count : '-'}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center text-indigo-600">
              <FileCheck className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gqt-neutral-500 uppercase">Approved For Drives</p>
              <h3 className="text-2xl font-bold text-emerald-600 mt-1">
                {metrics ? metrics.approved_count : '-'}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-emerald-50 flex items-center justify-center text-emerald-600">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gqt-neutral-500 uppercase">Closing in 7 Days</p>
              <h3 className="text-2xl font-bold text-rose-600 mt-1">
                {metrics ? metrics.deadlines_approaching_count : '-'}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
              <AlertCircle className="w-5 h-5" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filter and Search Bar */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2 relative">
              <Search className="w-4 h-4 text-gqt-neutral-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search by role title, required skills, location, or company..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="w-full pl-9 pr-4 py-2 border border-gqt-neutral-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              />
            </div>

            <div>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="">All Lifecycle States</option>
                <option value="DRAFT">Draft</option>
                <option value="PENDING_VERIFICATION">Pending Verification</option>
                <option value="UNDER_REVIEW">Under Review</option>
                <option value="CHANGES_REQUESTED">Changes Requested</option>
                <option value="VERIFIED">Verified (Ready for Head)</option>
                <option value="APPROVED">Approved (Locked)</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <div>
              <select
                value={typeFilter}
                onChange={(e) => {
                  setTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-3 py-2 border border-gqt-neutral-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-gqt-blue"
              >
                <option value="">All Employment Types</option>
                <option value="FULL_TIME">Full-Time</option>
                <option value="INTERNSHIP">Internship</option>
                <option value="INTERNSHIP_PPO">Internship + PPO</option>
                <option value="CONTRACT">Contract</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Directory Table */}
      {isLoading ? (
        <LoadingState message="Loading job requirement directory..." />
      ) : isError ? (
        <ErrorState
          title="Error Loading Requirements"
          message="Failed to fetch job requirements from server."
          onRetry={refetch}
        />
      ) : !jobsData?.data || jobsData.data.length === 0 ? (
        <EmptyState
          title="No Job Requirements Found"
          description={
            search || statusFilter || typeFilter
              ? 'No opportunities match your selected search or filter criteria.'
              : 'No corporate job requirements have been collected yet. Collect a requirement to start the verification workflow.'
          }
          action={
            canCreate ? (
              <Button variant="primary" size="sm" onClick={() => navigate('/jobs/new')}>
                Intake First Requirement
              </Button>
            ) : undefined
          }
        />
      ) : (
        <div className="bg-white rounded-xl shadow-card border border-gqt-neutral-200/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-gqt-neutral-50 text-gqt-neutral-600 font-semibold border-b border-gqt-neutral-200 uppercase text-xs tracking-wider">
                <tr>
                  <th className="py-3.5 px-4">Role Title & Company</th>
                  <th className="py-3.5 px-4">Location & Type</th>
                  <th className="py-3.5 px-4">Compensation (CTC)</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">5-Point Checklist</th>
                  <th className="py-3.5 px-4">Registration Cutoff</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gqt-neutral-200/70">
                {jobsData.data.map((job: JobRequirementListItem) => {
                  const progress = job.checklist_progress;
                  const isVerifiedComplete = progress?.is_complete;

                  return (
                    <tr
                      key={job.id}
                      className="hover:bg-blue-50/40 transition-colors cursor-pointer"
                      onClick={() => navigate(`/jobs/${job.id}`)}
                    >
                      <td className="py-3 px-4">
                        <div className="font-semibold text-gqt-navy hover:text-gqt-blue">
                          {job.title}
                        </div>
                        <div className="text-xs text-gqt-neutral-500 mt-0.5 flex items-center gap-1.5">
                          <span className="font-medium text-gqt-neutral-700">{job.company_name}</span>
                          <span>•</span>
                          <span className="text-gqt-neutral-400">{job.openings_count} openings</span>
                        </div>
                      </td>

                      <td className="py-3 px-4">
                        <div className="text-gqt-neutral-800">{job.location}</div>
                        <div className="text-xs text-gqt-neutral-500 capitalize">
                          {job.employment_type.toLowerCase().replace('_', ' ')} • {job.work_arrangement.toLowerCase()}
                        </div>
                      </td>

                      <td className="py-3 px-4 font-medium text-gqt-navy">
                        {formatSalary(job.min_salary, job.max_salary, job.salary_currency)}
                      </td>

                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={getStatusBadgeVariant(job.status)}
                          label={getStatusLabel(job.status)}
                        />
                      </td>

                      <td className="py-3 px-4">
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-medium text-gqt-neutral-700">
                              {progress ? `${progress.verified_mandatory} / ${progress.total_mandatory}` : '0 / 5'} Verified
                            </span>
                            <span className="text-gqt-neutral-400">{progress ? `${progress.percentage}%` : '0%'}</span>
                          </div>
                          <div className="w-28 bg-gqt-neutral-100 rounded-full h-1.5 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isVerifiedComplete ? 'bg-emerald-500' : 'bg-gqt-blue'
                              }`}
                              style={{ width: `${progress ? progress.percentage : 0}%` }}
                            />
                          </div>
                        </div>
                      </td>

                      <td className="py-3 px-4 text-xs font-medium text-gqt-neutral-700">
                        {formatDeadline(job.registration_deadline)}
                      </td>

                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/jobs/${job.id}`)}
                            title="View Verification Workspace"
                          >
                            <Eye className="w-4 h-4 text-gqt-neutral-600" />
                          </Button>
                          {canCreate && ['DRAFT', 'CHANGES_REQUESTED'].includes(job.status) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/jobs/${job.id}/edit`)}
                              title="Edit Requirement"
                            >
                              <Edit className="w-4 h-4 text-gqt-neutral-600" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => navigate(`/jobs/${job.id}`)}
                          >
                            <ChevronRight className="w-4 h-4 text-gqt-neutral-400" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {jobsData.meta && jobsData.meta.total_pages > 1 && (
            <div className="flex items-center justify-between px-4 py-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200">
              <span className="text-xs text-gqt-neutral-600">
                Page {jobsData.meta.current_page} of {jobsData.meta.total_pages} (Total {jobsData.meta.count} records)
              </span>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!jobsData.meta.previous}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={!jobsData.meta.next}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
