import React, { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, Navigate } from 'react-router-dom';
import {
  Briefcase,
  Building2,
  Calendar,
  Clock,
  MapPin,
  CheckCircle2,
  AlertCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  Search,
  FileText,
  AlertTriangle,
  Send,
  X,
  ShieldCheck,
  Award,
} from 'lucide-react';
import { useAuth } from '@/context/AuthContext';
import { studentsApi } from '@/api/studentsApi';
import { JobPublication, StudentApplication } from '@/types/students';
import { Card, CardContent } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge, StatusVariant } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { EmptyState } from '@/components/common/EmptyState';

type FilterTab = 'ALL' | 'OPEN' | 'APPLIED' | 'ELIGIBLE' | 'INELIGIBLE';

export const StudentDrivesPage: React.FC = () => {
  const { user, isLoading: isAuthLoading } = useAuth();
  const isStudent = Boolean(user?.roles?.includes('STUDENT'));
  const queryClient = useQueryClient();

  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState<FilterTab>('ALL');
  const [expandedOpportunityId, setExpandedOpportunityId] = useState<string | null>(null);

  // Application modal state
  const [selectedOpportunity, setSelectedOpportunity] = useState<JobPublication | null>(null);
  const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
  const [applyError, setApplyError] = useState<string | null>(null);
  const [applySuccessMessage, setApplySuccessMessage] = useState<string | null>(null);

  // Evaluation breakdown modal state
  const [viewingEvaluationApp, setViewingEvaluationApp] = useState<StudentApplication | null>(null);
  const [viewingPreviewPub, setViewingPreviewPub] = useState<JobPublication | null>(null);

  // 1. Fetch available publications (approved, dispatched/delivered opportunities)
  const {
    data: publications = [],
    isLoading: isPubsLoading,
    error: pubsError,
    refetch: refetchPubs,
  } = useQuery({
    queryKey: ['job-publications'],
    queryFn: () => studentsApi.listPublications(),
    enabled: isStudent,
  });

  // 2. Fetch logged-in student's existing applications
  const {
    data: myApplications = [],
    isLoading: isAppsLoading,
    error: appsError,
    refetch: refetchApps,
  } = useQuery({
    queryKey: ['student-applications'],
    queryFn: () => studentsApi.listApplications(),
    enabled: isStudent,
  });

  // 3. Fetch logged-in student's academic profile & resume status
  const {
    data: profile,
    isLoading: isProfileLoading,
    error: profileError,
    refetch: refetchProfile,
  } = useQuery({
    queryKey: ['student-profile-me'],
    queryFn: () => studentsApi.getProfileMe(),
    enabled: isStudent,
  });

  // Map of applications by job_requirement UUID
  const applicationsByJobId = useMemo(() => {
    const map = new Map<string, StudentApplication>();
    for (const app of myApplications) {
      map.set(app.job_requirement, app);
    }
    return map;
  }, [myApplications]);

  // Apply mutation with duplicate submission prevention
  const applyMutation = useMutation({
    mutationFn: (jobRequirementId: string) => studentsApi.applyForJob(jobRequirementId),
    onSuccess: (data: StudentApplication) => {
      setApplySuccessMessage(
        `Application submitted successfully for ${data.job_title} at ${data.company_name}! Deterministic eligibility verified: ${data.status_display}.`
      );
      setApplyError(null);
      setIsApplyModalOpen(false);
      setSelectedOpportunity(null);

      // Refresh applications cache to update card badges immediately
      queryClient.invalidateQueries({ queryKey: ['student-applications'] });
    },
    onError: (err: any) => {
      const serverMsg =
        err?.response?.data?.detail ||
        err?.response?.data?.job_requirement_id ||
        err?.message ||
        'Failed to submit application. Please try again or refresh the page.';
      setApplyError(typeof serverMsg === 'string' ? serverMsg : JSON.stringify(serverMsg));
    },
  });

  const handleOpenApplyModal = (pub: JobPublication) => {
    setApplyError(null);
    setSelectedOpportunity(pub);
    setIsApplyModalOpen(true);
  };

  const handleConfirmApply = () => {
    if (!selectedOpportunity) return;
    applyMutation.mutate(selectedOpportunity.job_requirement);
  };

  // Helper to format salary / compensation
  const formatSalary = (pub: JobPublication) => {
    if (pub.min_salary && pub.max_salary) {
      return `${pub.salary_currency || 'INR'} ${pub.min_salary} - ${pub.max_salary}`;
    }
    if (pub.min_salary) {
      return `${pub.salary_currency || 'INR'} ${pub.min_salary}`;
    }
    return 'As per corporate standards';
  };

  // Helper to check if opportunity registration is closed
  const isOpportunityClosed = (pub: JobPublication) => {
    if (!pub.registration_deadline) return false;
    return new Date(pub.registration_deadline).getTime() < Date.now();
  };

  // Filtered and searched opportunities
  const filteredPublications = useMemo(() => {
    return publications.filter((pub) => {
      const app = applicationsByJobId.get(pub.job_requirement);
      const isClosed = isOpportunityClosed(pub);

      // Search match across title, company, skills, location, target audience
      const searchLower = searchQuery.toLowerCase().trim();
      const matchesSearch =
        !searchLower ||
        pub.job_title.toLowerCase().includes(searchLower) ||
        pub.company_name.toLowerCase().includes(searchLower) ||
        (pub.location && pub.location.toLowerCase().includes(searchLower)) ||
        (pub.skills_required && pub.skills_required.toLowerCase().includes(searchLower)) ||
        pub.target_audience.toLowerCase().includes(searchLower);

      if (!matchesSearch) return false;

      // Status filter tab
      switch (activeFilter) {
        case 'OPEN':
          return !app && !isClosed;
        case 'APPLIED':
          return !!app;
        case 'ELIGIBLE':
          if (app) {
            return app.status === 'ELIGIBLE' || app.status === 'OVERRIDDEN';
          }
          return pub.eligibility_preview?.passed === true;
        case 'INELIGIBLE':
          if (app) {
            return app.status === 'INELIGIBLE';
          }
          return (
            pub.eligibility_preview?.passed === false &&
            pub.eligibility_preview?.status !== 'INCOMPLETE'
          );
        case 'ALL':
        default:
          return true;
      }
    });
  }, [publications, applicationsByJobId, searchQuery, activeFilter]);

  // Non-student staff access guard: redirect staff/admin accounts without genuine STUDENT role
  if (!isAuthLoading && !isStudent) {
    return <Navigate to="/access-denied" replace />;
  }

  // Loading state
  const isLoadingAll = isAuthLoading || isPubsLoading || isAppsLoading || isProfileLoading;
  if (isLoadingAll) {
    return (
      <div className="py-12">
        <LoadingState message="Loading corporate placement drives, active notices, and application status..." />
      </div>
    );
  }

  // Error state
  const anyError = pubsError || appsError || profileError;
  if (anyError) {
    return (
      <div className="py-12">
        <ErrorState
          title="Unable to load Placement Drives"
          message="An error occurred communicating with the GQT HRMS server while retrieving published recruitment opportunities."
          onRetry={() => {
            refetchPubs();
            refetchApps();
            refetchProfile();
          }}
        />
      </div>
    );
  }

  const hasActiveResume = Boolean(profile?.current_resume);

  return (
    <div className="space-y-6">
      {/* Page Title & Overview */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gqt-navy flex items-center gap-2.5">
            <Briefcase className="w-7 h-7 text-gqt-blue" />
            Placement Drives & Corporate Opportunities
          </h1>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            Browse verified campus recruitment opportunities certified by the Placement Office and submit your application.
          </p>
        </div>

        {/* Student Profile & Resume Summary Card */}
        {profile && (
          <div className="flex items-center gap-3 bg-white border border-gqt-neutral-200 rounded-lg p-3 shadow-xs shrink-0">
            <div className="text-xs space-y-0.5">
              <div className="font-semibold text-gqt-charcoal">
                {profile.full_name} ({profile.roll_number})
              </div>
              <div className="text-gqt-neutral-500">
                {profile.department} • CGPA {profile.cgpa}
              </div>
            </div>
            {hasActiveResume ? (
              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Resume v{profile.current_resume?.version_number} Active
              </span>
            ) : (
              <Link
                to="/students/profile"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors"
              >
                <AlertCircle className="w-3.5 h-3.5" />
                Resume Missing (Upload)
              </Link>
            )}
          </div>
        )}
      </div>

      {/* Missing Resume Alert Banner */}
      {!hasActiveResume && (
        <div
          role="alert"
          className="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-900 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-xs"
        >
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <h4 className="text-sm font-bold text-amber-950">Resume Required for Applications</h4>
              <p className="text-xs text-amber-800 mt-0.5">
                The GQT deterministic eligibility verification engine requires an active uploaded PDF resume before you can apply for placement drives.
              </p>
            </div>
          </div>
          <Link to="/students/profile">
            <Button size="sm" variant="outline" className="border-amber-300 bg-white text-amber-900 hover:bg-amber-100 shrink-0">
              <FileText className="w-3.5 h-3.5 mr-1" />
              Upload Resume
            </Button>
          </Link>
        </div>
      )}

      {/* Success Notification Banner */}
      {applySuccessMessage && (
        <div
          role="status"
          className="p-4 rounded-xl border border-emerald-200 bg-emerald-50 text-emerald-900 flex items-start justify-between gap-3 shadow-xs"
        >
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <p className="text-sm font-medium">{applySuccessMessage}</p>
          </div>
          <button
            onClick={() => setApplySuccessMessage(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs p-1 rounded-md"
            aria-label="Dismiss alert"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Global Error Banner (e.g. from failed apply attempt outside modal) */}
      {applyError && !isApplyModalOpen && (
        <div
          role="alert"
          className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 flex items-start justify-between gap-3 shadow-xs"
        >
          <div className="flex items-center gap-2.5">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <p className="text-sm font-medium">{applyError}</p>
          </div>
          <button
            onClick={() => setApplyError(null)}
            className="text-rose-700 hover:text-rose-900 text-xs p-1 rounded-md"
            aria-label="Dismiss alert"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search Bar & Filter Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-white p-4 rounded-xl border border-gqt-neutral-200 shadow-xs">
        {/* Search input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gqt-neutral-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search opportunities by job title, company name, skills, or location..."
            className="w-full pl-9 pr-4 py-2 border border-gqt-neutral-300 rounded-lg text-sm text-gqt-charcoal placeholder:text-gqt-neutral-400 focus:outline-none focus:ring-2 focus:ring-gqt-blue focus:border-transparent transition-all"
            aria-label="Search placement drives"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gqt-neutral-400 hover:text-gqt-charcoal text-xs"
              aria-label="Clear search query"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0" role="tablist" aria-label="Drive status filters">
          {(
            [
              { key: 'ALL', label: 'All Opportunities' },
              { key: 'OPEN', label: 'Open to Apply' },
              { key: 'APPLIED', label: 'Applied' },
              { key: 'ELIGIBLE', label: 'Eligible' },
              { key: 'INELIGIBLE', label: 'Ineligible' },
            ] as const
          ).map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeFilter === tab.key}
              onClick={() => setActiveFilter(tab.key)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${activeFilter === tab.key
                ? 'bg-gqt-navy text-white shadow-xs'
                : 'bg-gqt-neutral-100 text-gqt-neutral-600 hover:bg-gqt-neutral-200 hover:text-gqt-charcoal'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Directory Content List */}
      {publications.length === 0 ? (
        <EmptyState
          title="No Placement Drives Available"
          description="There are currently no active corporate recruitment announcements published for your cohort. Please check back regularly as new drives are scheduled."
        />
      ) : filteredPublications.length === 0 ? (
        <EmptyState
          title="No Opportunities Match Your Filter"
          description="We couldn't find any placement drives matching your search keywords or selected status filter."
          action={
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchQuery('');
                setActiveFilter('ALL');
              }}
            >
              Reset Filters
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 gap-5">
          {filteredPublications.map((pub) => {
            const existingApp = applicationsByJobId.get(pub.job_requirement);
            const isClosed = isOpportunityClosed(pub);
            const isExpanded = expandedOpportunityId === pub.id;

            // Application Status Badge Variant
            let statusVariant: StatusVariant = 'info';
            let statusText = 'Not Applied';

            if (existingApp) {
              switch (existingApp.status) {
                case 'ELIGIBLE':
                  statusVariant = 'success';
                  statusText = 'Eligible — Meets Criteria';
                  break;
                case 'INELIGIBLE':
                  statusVariant = 'danger';
                  statusText = 'Ineligible — Criteria Not Satisfied';
                  break;
                case 'OVERRIDDEN':
                  statusVariant = 'warning';
                  statusText = 'Overridden — Placement Certified';
                  break;
                case 'WITHDRAWN':
                  statusVariant = 'neutral';
                  statusText = 'Withdrawn';
                  break;
                case 'APPLIED':
                default:
                  statusVariant = 'warning';
                  statusText = 'Applied — Verification Pending';
                  break;
              }
            } else if (isClosed) {
              statusVariant = 'neutral';
              statusText = 'Registration Closed';
            } else if (pub.eligibility_preview) {
              if (pub.eligibility_preview.passed) {
                statusVariant = 'success';
                statusText = 'Eligible to Apply (Preview)';
              } else if (pub.eligibility_preview.status === 'INCOMPLETE') {
                statusVariant = 'neutral';
                statusText = 'Open — Academic Details Incomplete';
              } else {
                statusVariant = 'danger';
                statusText = 'Ineligible (Preview)';
              }
            } else {
              statusVariant = 'info';
              statusText = 'Open for Application';
            }

            return (
              <Card
                key={pub.id}
                className={`transition-all border-l-4 ${existingApp?.status === 'ELIGIBLE'
                  ? 'border-l-emerald-500'
                  : existingApp?.status === 'INELIGIBLE'
                    ? 'border-l-rose-500'
                    : existingApp?.status === 'OVERRIDDEN'
                      ? 'border-l-amber-500'
                      : existingApp
                        ? 'border-l-blue-500'
                        : isClosed
                          ? 'border-l-gqt-neutral-300'
                          : pub.eligibility_preview?.passed === true
                            ? 'border-l-emerald-500'
                            : pub.eligibility_preview?.passed === false
                              ? 'border-l-rose-500'
                              : 'border-l-gqt-navy'
                  }`}
              >
                <CardContent className="p-6">
                  {/* Top Meta Bar */}
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wide">
                        <Building2 className="w-4 h-4 text-gqt-blue shrink-0" />
                        <span>{pub.company_name}</span>
                        <span>•</span>
                        <span>{pub.channel_display}</span>
                      </div>
                      <h2 className="text-lg font-bold text-gqt-navy mt-1">{pub.job_title}</h2>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <StatusBadge variant={statusVariant} label={statusText} />
                    </div>
                  </div>

                  {/* Metadata Chips Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 py-3 border-y border-gqt-neutral-100 text-xs">
                    <div className="flex items-center gap-2 text-gqt-neutral-700">
                      <MapPin className="w-4 h-4 text-gqt-neutral-400 shrink-0" />
                      <div>
                        <div className="text-gqt-neutral-400">Location</div>
                        <div className="font-medium text-gqt-charcoal truncate">
                          {pub.location || 'Pan India / TBD'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-gqt-neutral-700">
                      <Briefcase className="w-4 h-4 text-gqt-neutral-400 shrink-0" />
                      <div>
                        <div className="text-gqt-neutral-400">Employment Type</div>
                        <div className="font-medium text-gqt-charcoal truncate">
                          {pub.employment_type_display || pub.employment_type || 'Full-Time'}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-gqt-neutral-700">
                      <Award className="w-4 h-4 text-gqt-neutral-400 shrink-0" />
                      <div>
                        <div className="text-gqt-neutral-400">Compensation (CTC)</div>
                        <div className="font-medium text-gqt-charcoal truncate">{formatSalary(pub)}</div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-gqt-neutral-700">
                      <Clock className="w-4 h-4 text-gqt-neutral-400 shrink-0" />
                      <div>
                        <div className="text-gqt-neutral-400">Deadline</div>
                        <div
                          className={`font-medium truncate ${isClosed ? 'text-rose-600 font-bold' : 'text-gqt-charcoal'
                            }`}
                        >
                          {pub.registration_deadline
                            ? new Date(pub.registration_deadline).toLocaleDateString(undefined, {
                              day: 'numeric',
                              month: 'short',
                              year: 'numeric',
                            })
                            : 'Open until filled'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Target Audience & Quick Criteria Notice */}
                  <div className="mt-3.5 space-y-2 text-xs">
                    <div className="flex items-start gap-2 text-gqt-neutral-600 bg-gqt-neutral-50/80 p-2.5 rounded-lg border border-gqt-neutral-200">
                      <ShieldCheck className="w-4 h-4 text-gqt-blue shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-gqt-charcoal">Eligible Cohort: </span>
                        {pub.target_audience}
                        {pub.min_cgpa && (
                          <span className="ml-2 font-medium text-gqt-navy">
                            (Min CGPA: {pub.min_cgpa})
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Announcement Subject & Summary */}
                    {pub.subject && (
                      <p className="text-gqt-neutral-600 font-medium">
                        <span className="font-bold text-gqt-charcoal">Notice Headline: </span>
                        {pub.subject}
                      </p>
                    )}
                  </div>

                  {/* Expandable Details Section */}
                  {isExpanded && (
                    <div className="mt-4 pt-4 border-t border-gqt-neutral-200 space-y-3.5 text-xs text-gqt-neutral-700 animate-fadeIn">
                      {/* Detailed Announcement Message */}
                      {pub.message_body && (
                        <div>
                          <h4 className="font-bold text-gqt-navy mb-1">Official Notice Details</h4>
                          <div className="bg-white p-3 rounded-lg border border-gqt-neutral-200 whitespace-pre-line text-gqt-charcoal leading-relaxed font-sans">
                            {pub.message_body}
                          </div>
                        </div>
                      )}

                      {/* Job Description */}
                      {pub.job_description && (
                        <div>
                          <h4 className="font-bold text-gqt-navy mb-1">Role Description & Responsibilities</h4>
                          <p className="bg-gqt-neutral-50 p-3 rounded-lg border border-gqt-neutral-200 leading-relaxed text-gqt-charcoal whitespace-pre-line">
                            {pub.job_description}
                          </p>
                        </div>
                      )}

                      {/* Skills & Competencies */}
                      {pub.skills_required && (
                        <div>
                          <h4 className="font-bold text-gqt-navy mb-1">Skills & Technical Competencies</h4>
                          <p className="bg-gqt-neutral-50 p-2.5 rounded-lg border border-gqt-neutral-200 leading-relaxed text-gqt-charcoal">
                            {pub.skills_required}
                          </p>
                        </div>
                      )}

                      {/* Bond Details if applicable */}
                      {pub.has_bond && (
                        <div className="bg-amber-50/70 p-3 rounded-lg border border-amber-200 text-amber-900">
                          <span className="font-bold">Service Agreement / Bond: </span>
                          {pub.bond_details || 'Service commitment required as per corporate policy.'}
                        </div>
                      )}

                      {/* Tentative Interview Date */}
                      {pub.interview_date && (
                        <div className="flex items-center gap-2 text-gqt-neutral-600">
                          <Calendar className="w-4 h-4 text-gqt-blue shrink-0" />
                          <span>
                            <strong className="text-gqt-charcoal">Tentative Drive Date: </strong>
                            {new Date(pub.interview_date).toLocaleDateString(undefined, {
                              day: 'numeric',
                              month: 'long',
                              year: 'numeric',
                            })}
                          </span>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions & Decision Footer */}
                  <div className="mt-4 pt-3 border-t border-gqt-neutral-100 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                    {/* Left details toggle */}
                    <button
                      type="button"
                      onClick={() => setExpandedOpportunityId(isExpanded ? null : pub.id)}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-gqt-blue hover:text-gqt-navy transition-colors self-start sm:self-center"
                      aria-expanded={isExpanded}
                    >
                      {isExpanded ? (
                        <>
                          <ChevronUp className="w-4 h-4" />
                          Hide Full Drive Details
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-4 h-4" />
                          View Full Drive Details
                        </>
                      )}
                    </button>

                    {/* Right Apply / Status Actions */}
                    <div className="flex items-center gap-2 self-end sm:self-center flex-wrap justify-end">
                      {existingApp ? (
                        <div className="flex items-center gap-2">
                          {existingApp.eligibility_evaluation && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setViewingEvaluationApp(existingApp)}
                              className="text-xs border-gqt-blue text-gqt-blue hover:bg-gqt-blue-light"
                            >
                              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-gqt-blue" />
                              View Eligibility Breakdown
                            </Button>
                          )}
                          <span className="text-xs font-medium text-gqt-neutral-500">
                            Applied on {new Date(existingApp.applied_at).toLocaleDateString()}
                          </span>
                        </div>
                      ) : isClosed ? (
                        <Button size="sm" variant="outline" disabled className="text-xs opacity-60">
                          Registration Closed
                        </Button>
                      ) : (
                        <>
                          {pub.eligibility_preview && (
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => setViewingPreviewPub(pub)}
                              className="text-xs border-gqt-neutral-300 text-gqt-charcoal hover:bg-gqt-neutral-50"
                            >
                              <ShieldCheck className="w-3.5 h-3.5 mr-1 text-gqt-blue" />
                              View Eligibility Preview
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="primary"
                            onClick={() => handleOpenApplyModal(pub)}
                            disabled={!hasActiveResume}
                            leftIcon={<Send className="w-3.5 h-3.5" />}
                            className="bg-gqt-navy hover:bg-gqt-navy-light text-white text-xs"
                          >
                            Apply for Opportunity
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Confirmation & Application Submission Modal */}
      {isApplyModalOpen && selectedOpportunity && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="apply-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-gqt-neutral-200">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="apply-modal-title" className="text-base font-bold">
                  Confirm Drive Application
                </h3>
              </div>
              <button
                onClick={() => setIsApplyModalOpen(false)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close modal"
                disabled={applyMutation.isPending}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal">
              {/* Opportunity Summary */}
              <div className="bg-gqt-neutral-50 p-3.5 rounded-lg border border-gqt-neutral-200 space-y-1.5">
                <div className="text-gqt-neutral-500 font-semibold uppercase">Position & Company</div>
                <div className="text-sm font-bold text-gqt-navy">{selectedOpportunity.job_title}</div>
                <div className="font-medium text-gqt-charcoal">{selectedOpportunity.company_name}</div>
                <div className="text-gqt-neutral-500 mt-1">
                  Location: {selectedOpportunity.location || 'Not Specified'} • Package: {formatSalary(selectedOpportunity)}
                </div>
              </div>

              {/* Student Academic & Resume Info being attached */}
              {profile && (
                <div className="bg-blue-50/60 p-3.5 rounded-lg border border-blue-200 space-y-2">
                  <div className="font-bold text-gqt-navy flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-gqt-blue" />
                    Applicant Academic Credentials Submitted
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-gqt-neutral-700">
                    <div>
                      <span className="text-gqt-neutral-500">Roll Number: </span>
                      <strong className="text-gqt-charcoal">{profile.roll_number}</strong>
                    </div>
                    <div>
                      <span className="text-gqt-neutral-500">Department: </span>
                      <strong className="text-gqt-charcoal">{profile.department}</strong>
                    </div>
                    <div>
                      <span className="text-gqt-neutral-500">Current CGPA: </span>
                      <strong className="text-gqt-charcoal">{profile.cgpa}</strong>
                    </div>
                    <div>
                      <span className="text-gqt-neutral-500">Active Backlogs: </span>
                      <strong className="text-gqt-charcoal">{profile.active_backlogs}</strong>
                    </div>
                    <div>
                      <span className="text-gqt-neutral-500">Graduation Batch: </span>
                      <strong className="text-gqt-charcoal">{profile.graduation_year}</strong>
                    </div>
                    <div>
                      <span className="text-gqt-neutral-500">Resume Attached: </span>
                      <strong className="text-emerald-700">
                        {profile.current_resume?.file_name || `v${profile.current_resume?.version_number}`}
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Deterministic Eligibility Engine Notice */}
              <div className="p-3 rounded-lg bg-gqt-neutral-100 text-gqt-neutral-600 leading-relaxed">
                <span className="font-bold text-gqt-charcoal">Deterministic Evaluation Notice: </span>
                Upon clicking Submit, the GQT eligibility engine evaluates your discipline, CGPA, backlogs, and graduation year against the company requirements. Your initial application qualification status will be determined immediately.
              </div>

              {/* Error Alert inside Modal */}
              {applyError && (
                <div role="alert" className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-2">
                  <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  <span className="font-medium">{applyError}</span>
                </div>
              )}
            </div>

            {/* Modal Actions */}
            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex items-center justify-end gap-2.5">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsApplyModalOpen(false)}
                disabled={applyMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                isLoading={applyMutation.isPending}
                onClick={handleConfirmApply}
                className="bg-gqt-navy hover:bg-gqt-navy-light text-white"
              >
                {applyMutation.isPending ? 'Verifying & Submitting...' : 'Confirm & Apply'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Criterion-by-Criterion Evaluation Details Modal */}
      {viewingEvaluationApp && viewingEvaluationApp.eligibility_evaluation && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="eval-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full overflow-hidden border border-gqt-neutral-200">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="eval-modal-title" className="text-base font-bold">
                  Eligibility Engine Evaluation Breakdown
                </h3>
              </div>
              <button
                onClick={() => setViewingEvaluationApp(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close evaluation modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal max-h-[75vh] overflow-y-auto">
              {/* Header summary */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                <div>
                  <div className="font-bold text-gqt-navy text-sm">{viewingEvaluationApp.job_title}</div>
                  <div className="text-gqt-neutral-500">{viewingEvaluationApp.company_name}</div>
                </div>
                <StatusBadge
                  variant={
                    viewingEvaluationApp.status === 'ELIGIBLE'
                      ? 'success'
                      : viewingEvaluationApp.status === 'INELIGIBLE'
                        ? 'danger'
                        : viewingEvaluationApp.status === 'OVERRIDDEN'
                          ? 'warning'
                          : 'neutral'
                  }
                  label={viewingEvaluationApp.status_display}
                />
              </div>

              {/* Manual Override Justification Callout if applicable */}
              {viewingEvaluationApp.eligibility_evaluation.is_overridden && (
                <div className="p-3.5 rounded-lg bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-amber-950">
                    <ShieldCheck className="w-4 h-4 text-amber-600" />
                    Placement Officer Manual Override Sign-off
                  </div>
                  <p className="italic">
                    "{viewingEvaluationApp.eligibility_evaluation.override_reason}"
                  </p>
                  <div className="text-amber-800 text-[11px] pt-1">
                    Certified by {viewingEvaluationApp.eligibility_evaluation.override_by_name || 'Placement Officer'}
                    {viewingEvaluationApp.eligibility_evaluation.override_at &&
                      ` on ${new Date(
                        viewingEvaluationApp.eligibility_evaluation.override_at
                      ).toLocaleString()}`}
                  </div>
                </div>
              )}

              {/* Criterion Breakdown Table */}
              <div className="space-y-2.5">
                <div className="font-bold text-gqt-navy text-xs uppercase tracking-wider">
                  Evaluated Academic Criteria
                </div>
                <div className="space-y-2">
                  {viewingEvaluationApp.eligibility_evaluation.evaluation_details?.map(
                    (detail, idx) => (
                      <div
                        key={idx}
                        className={`p-3 rounded-lg border ${detail.passed
                          ? 'bg-emerald-50/40 border-emerald-200'
                          : 'bg-rose-50/40 border-rose-200'
                          }`}
                      >
                        <div className="flex items-center justify-between font-semibold">
                          <span className="text-gqt-charcoal">{detail.criterion}</span>
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-bold ${detail.passed ? 'text-emerald-700' : 'text-rose-700'
                              }`}
                          >
                            {detail.passed ? (
                              <>
                                <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                              </>
                            ) : (
                              <>
                                <XCircle className="w-3.5 h-3.5" /> Not Met
                              </>
                            )}
                          </span>
                        </div>
                        <div className="mt-1.5 grid grid-cols-2 gap-2 text-[11px] text-gqt-neutral-600">
                          <div>
                            <span className="text-gqt-neutral-500">Student Value: </span>
                            <span className="font-medium text-gqt-charcoal">{detail.student_value}</span>
                          </div>
                          <div>
                            <span className="text-gqt-neutral-500">Requirement: </span>
                            <span className="font-medium text-gqt-charcoal">{detail.required_value}</span>
                          </div>
                        </div>
                        <p className="mt-1 text-[11px] text-gqt-neutral-600 leading-relaxed">
                          {detail.details}
                        </p>
                      </div>
                    )
                  )}
                </div>
              </div>

              {/* Evaluation timestamp */}
              <div className="text-right text-[11px] text-gqt-neutral-400">
                Evaluation timestamp:{' '}
                {new Date(
                  viewingEvaluationApp.eligibility_evaluation.evaluated_at
                ).toLocaleString()}
              </div>
            </div>

            <div className="p-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex justify-end">
              <Button size="sm" variant="outline" onClick={() => setViewingEvaluationApp(null)}>
                Close Breakdown
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Pre-Application Eligibility Preview Breakdown Modal */}
      {viewingPreviewPub && viewingPreviewPub.eligibility_preview && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="preview-modal-title"
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs animate-fadeIn"
        >
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full overflow-hidden border border-gqt-neutral-200">
            <div className="bg-gqt-navy p-4 text-white flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-gqt-blue-light" />
                <h3 id="preview-modal-title" className="text-base font-bold">
                  Pre-Application Eligibility Preview
                </h3>
              </div>
              <button
                onClick={() => setViewingPreviewPub(null)}
                className="text-white/80 hover:text-white p-1 rounded-md"
                aria-label="Close preview modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal max-h-[75vh] overflow-y-auto">
              {/* Header summary */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                <div>
                  <div className="font-bold text-gqt-navy text-sm">{viewingPreviewPub.job_title}</div>
                  <div className="text-gqt-neutral-500">{viewingPreviewPub.company_name}</div>
                </div>
                <StatusBadge
                  variant={
                    viewingPreviewPub.eligibility_preview.passed
                      ? 'success'
                      : viewingPreviewPub.eligibility_preview.status === 'INCOMPLETE'
                        ? 'neutral'
                        : 'danger'
                  }
                  label={
                    viewingPreviewPub.eligibility_preview.passed
                      ? 'Eligible to Apply'
                      : viewingPreviewPub.eligibility_preview.status === 'INCOMPLETE'
                        ? 'Incomplete Academic Details'
                        : 'Criteria Not Met'
                  }
                />
              </div>

              {/* Informational Pre-Application Callout */}
              <div className="p-3.5 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 space-y-1">
                <div className="font-bold flex items-center gap-1.5 text-blue-950">
                  <ShieldCheck className="w-4 h-4 text-blue-600" />
                  Pre-Application Deterministic Evaluation
                </div>
                <p className="text-[11px] leading-relaxed text-blue-800">
                  This preview assesses your verified student profile (branch, CGPA, backlogs, batch) against the company criteria. Viewing this preview does not create an application record or notify the company. Final verification is locked upon application submission.
                </p>
              </div>

              {/* Criterion Breakdown Table */}
              <div className="space-y-2.5">
                <div className="font-bold text-gqt-navy text-xs uppercase tracking-wider">
                  Evaluated Academic Criteria
                </div>
                <div className="space-y-2">
                  {viewingPreviewPub.eligibility_preview.details?.map((detail, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border ${detail.passed
                        ? 'bg-emerald-50/40 border-emerald-200'
                        : 'bg-rose-50/40 border-rose-200'
                        }`}
                    >
                      <div className="flex items-center justify-between font-semibold">
                        <span className="text-gqt-charcoal">{detail.criterion}</span>
                        <span
                          className={`inline-flex items-center gap-1 text-[11px] font-bold ${detail.passed ? 'text-emerald-700' : 'text-rose-700'
                            }`}
                        >
                          {detail.passed ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                            </>
                          ) : (
                            <>
                              <XCircle className="w-3.5 h-3.5" /> Not Met
                            </>
                          )}
                        </span>
                      </div>
                      <div className="mt-1.5 grid grid-cols-2 gap-2 text-[11px] text-gqt-neutral-600">
                        <div>
                          <span className="text-gqt-neutral-500">Your Record: </span>
                          <span className="font-medium text-gqt-charcoal">
                            {detail.student_value || 'N/A'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gqt-neutral-500">Requirement: </span>
                          <span className="font-medium text-gqt-charcoal">
                            {detail.required_value || 'None'}
                          </span>
                        </div>
                      </div>
                      <p className="mt-1 text-[11px] text-gqt-neutral-600 leading-relaxed">
                        {detail.details}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="p-3 bg-gqt-neutral-50 border-t border-gqt-neutral-200 flex justify-between items-center">
              <Button size="sm" variant="outline" onClick={() => setViewingPreviewPub(null)}>
                Close Preview
              </Button>
              {!applicationsByJobId.get(viewingPreviewPub.job_requirement) && !isOpportunityClosed(viewingPreviewPub) && (
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => {
                    const pubToApply = viewingPreviewPub;
                    setViewingPreviewPub(null);
                    handleOpenApplyModal(pubToApply);
                  }}
                  disabled={!hasActiveResume}
                  leftIcon={<Send className="w-3.5 h-3.5" />}
                  className="bg-gqt-navy hover:bg-gqt-navy-light text-white text-xs"
                >
                  Proceed to Apply
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
