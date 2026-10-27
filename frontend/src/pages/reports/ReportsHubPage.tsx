import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Building2,
  GraduationCap,
  Award,
  TrendingUp,
  Calendar,
  Download,
  Filter,
  RefreshCw,
  AlertCircle,
  CheckCircle2,
  Clock,
  Briefcase,
  Users,
  Percent,
  IndianRupee,
  ShieldAlert,
  Info,
} from 'lucide-react';
import { Card, CardHeader, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { useAuth } from '../../context/AuthContext';
import { reportsApi, downloadCsvBlob } from '../../api/reportsApi';
import {
  CompanyReportsData,
  CompanyReportsFilter,
  StudentReportsData,
  StudentReportsFilter,
  StudentSelfReportSummary,
  PlacementReportsData,
  PlacementReportsFilter,
  PerformanceReportsData,
  MonthlyStatisticsData,
} from '../../types/reports';

type ReportTab = 'company' | 'students' | 'placements' | 'performance' | 'monthly';

export const ReportsHubPage: React.FC = () => {
  const { hasAnyRole, hasRole } = useAuth();

  const isStaff = hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER']);
  const isHROnly = !isStaff && hasRole('HR_RELATIONSHIP_MGR');
  const isAuditor = hasRole('AUDITOR');
  const isStudent = !isStaff && !isHROnly && !isAuditor && hasRole('STUDENT');

  const [activeTab, setActiveTab] = useState<ReportTab>('company');
  const [isLoading, setIsLoading] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Datasets
  const [companyData, setCompanyData] = useState<CompanyReportsData | null>(null);
  const [studentData, setStudentData] = useState<StudentReportsData | null>(null);
  const [placementData, setPlacementData] = useState<PlacementReportsData | null>(null);
  const [performanceData, setPerformanceData] = useState<PerformanceReportsData | null>(null);
  const [monthlyData, setMonthlyData] = useState<MonthlyStatisticsData | null>(null);
  const [studentSelfData, setStudentSelfData] = useState<StudentSelfReportSummary | null>(null);

  // Filters
  const [companyTier, setCompanyTier] = useState<string>('');
  const [companyDomain, setCompanyDomain] = useState<string>('');
  const [companyDateFrom, setCompanyDateFrom] = useState<string>('');
  const [companyDateTo, setCompanyDateTo] = useState<string>('');

  const [studentDept, setStudentDept] = useState<string>('');
  const [studentYear, setStudentYear] = useState<string>('');
  const [studentVerified, setStudentVerified] = useState<string>('ALL');
  const [studentCertified, setStudentCertified] = useState<string>('ALL');
  const [studentPlacedOnly, setStudentPlacedOnly] = useState<boolean>(false);

  const [placementStatus, setPlacementStatus] = useState<string>('');
  const [offerStatus, setOfferStatus] = useState<string>('');
  const [joiningStatus, setJoiningStatus] = useState<string>('');

  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);

  // Load dataset for active tab
  const fetchActiveTabReport = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (isStudent) {
        const selfData = await reportsApi.getStudentSelfReport();
        setStudentSelfData(selfData);
        setIsLoading(false);
        return;
      }

      if (activeTab === 'company') {
        const filters: CompanyReportsFilter = {};
        if (companyTier) filters.tier = companyTier;
        if (companyDomain) filters.industry_domain = companyDomain;
        if (companyDateFrom) filters.date_from = companyDateFrom;
        if (companyDateTo) filters.date_to = companyDateTo;
        const res = await reportsApi.getCompanyReports(filters);
        setCompanyData(res);
      } else if (activeTab === 'students') {
        const filters: StudentReportsFilter = {};
        if (studentDept) filters.department = studentDept;
        if (studentYear) filters.passing_year = parseInt(studentYear, 10);
        if (studentVerified === 'TRUE') filters.is_verified = true;
        if (studentVerified === 'FALSE') filters.is_verified = false;
        if (studentCertified === 'TRUE') filters.is_certified = true;
        if (studentCertified === 'FALSE') filters.is_certified = false;
        if (studentPlacedOnly) filters.placed_only = true;
        const res = await reportsApi.getStudentReports(filters);
        setStudentData(res);
      } else if (activeTab === 'placements') {
        const filters: PlacementReportsFilter = {};
        if (placementStatus) filters.status = placementStatus;
        if (offerStatus) filters.offer_status = offerStatus;
        if (joiningStatus) filters.joining_status = joiningStatus;
        const res = await reportsApi.getPlacementReports(filters);
        setPlacementData(res);
      } else if (activeTab === 'performance') {
        const res = await reportsApi.getPerformanceReports({});
        setPerformanceData(res);
      } else if (activeTab === 'monthly') {
        const res = await reportsApi.getMonthlyStatistics({
          year: selectedYear,
          month: selectedMonth,
        });
        setMonthlyData(res);
      }
    } catch (err: any) {
      console.error('Failed to load report data:', err);
      setError(err?.response?.data?.detail || 'Failed to generate report dataset. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [
    isStudent,
    activeTab,
    companyTier,
    companyDomain,
    companyDateFrom,
    companyDateTo,
    studentDept,
    studentYear,
    studentVerified,
    studentCertified,
    studentPlacedOnly,
    placementStatus,
    offerStatus,
    joiningStatus,
    selectedYear,
    selectedMonth,
  ]);

  useEffect(() => {
    fetchActiveTabReport();
  }, [fetchActiveTabReport]);

  // CSV Export Handlers
  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      if (activeTab === 'company') {
        const filters: CompanyReportsFilter = {};
        if (companyTier) filters.tier = companyTier;
        if (companyDomain) filters.industry_domain = companyDomain;
        if (companyDateFrom) filters.date_from = companyDateFrom;
        if (companyDateTo) filters.date_to = companyDateTo;
        const blob = await reportsApi.exportCompanyReportsCsv(filters);
        downloadCsvBlob(blob, `gqt_company_reports_${new Date().toISOString().slice(0, 10)}.csv`);
      } else if (activeTab === 'students') {
        const filters: StudentReportsFilter = {};
        if (studentDept) filters.department = studentDept;
        if (studentYear) filters.passing_year = parseInt(studentYear, 10);
        if (studentVerified === 'TRUE') filters.is_verified = true;
        if (studentVerified === 'FALSE') filters.is_verified = false;
        if (studentCertified === 'TRUE') filters.is_certified = true;
        if (studentCertified === 'FALSE') filters.is_certified = false;
        if (studentPlacedOnly) filters.placed_only = true;
        const blob = await reportsApi.exportStudentReportsCsv(filters);
        downloadCsvBlob(blob, `gqt_student_reports_${new Date().toISOString().slice(0, 10)}.csv`);
      } else if (activeTab === 'placements') {
        const filters: PlacementReportsFilter = {};
        if (placementStatus) filters.status = placementStatus;
        if (offerStatus) filters.offer_status = offerStatus;
        if (joiningStatus) filters.joining_status = joiningStatus;
        const blob = await reportsApi.exportPlacementReportsCsv(filters);
        downloadCsvBlob(blob, `gqt_placement_reports_${new Date().toISOString().slice(0, 10)}.csv`);
      } else if (activeTab === 'performance') {
        const blob = await reportsApi.exportPerformanceReportsCsv({});
        downloadCsvBlob(blob, `gqt_recruitment_funnel_${new Date().toISOString().slice(0, 10)}.csv`);
      } else if (activeTab === 'monthly') {
        const blob = await reportsApi.exportMonthlyStatisticsCsv({
          year: selectedYear,
          month: selectedMonth,
        });
        downloadCsvBlob(blob, `gqt_monthly_statistics_${selectedYear}_${selectedMonth}.csv`);
      }
    } catch (err: any) {
      console.error('Export failed:', err);
      alert('Failed to generate secure CSV export. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  // Render Student Self-Report Isolated View
  if (isStudent) {
    return (
      <div className="space-y-6">
        <div className="bg-gradient-to-r from-gqt-navy via-gqt-navy-light to-gqt-blue rounded-2xl p-8 text-white shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-white border border-white/20 mb-3">
                <GraduationCap className="w-3.5 h-3.5" />
                Candidate Placement Trajectory
              </span>
              <h1 className="text-3xl font-extrabold tracking-tight">Personal Placement & Readiness Report</h1>
              <p className="text-gqt-neutral-200 mt-1 max-w-2xl text-sm">
                Real-time tracking of your institutional academic verification, Step 23 Placement Readiness Certification, interview participation, and offer status.
              </p>
            </div>
            <Button
              variant="outline"
              onClick={fetchActiveTabReport}
              disabled={isLoading}
              className="bg-white/10 border-white/30 text-white hover:bg-white/20 self-start md:self-auto"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh My Summary
            </Button>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        )}

        {isLoading ? (
          <div className="flex justify-center items-center py-20 text-gqt-neutral-500">
            <RefreshCw className="w-8 h-8 animate-spin text-gqt-blue" />
            <span className="ml-3 font-medium">Generating your placement trajectory summary...</span>
          </div>
        ) : studentSelfData ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Profile Overview Card */}
            <Card className="lg:col-span-1 shadow-sm border-gqt-neutral-200">
              <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gqt-blue/10 text-gqt-blue flex items-center justify-center font-bold text-lg">
                    {studentSelfData.full_name?.charAt(0) || 'S'}
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-gqt-navy">{studentSelfData.full_name}</h2>
                    <p className="text-xs text-gqt-neutral-500 font-mono">USN: {studentSelfData.usn}</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4 pt-5">
                <div className="flex justify-between items-center text-sm py-1 border-b border-gqt-neutral-100">
                  <span className="text-gqt-neutral-500 font-medium">Department</span>
                  <span className="font-semibold text-gqt-navy">{studentSelfData.department || '—'}</span>
                </div>
                <div className="flex justify-between items-center text-sm py-1 border-b border-gqt-neutral-100">
                  <span className="text-gqt-neutral-500 font-medium">Passing Year</span>
                  <span className="font-semibold text-gqt-navy">{studentSelfData.passing_year}</span>
                </div>
                <div className="flex justify-between items-center text-sm py-1 border-b border-gqt-neutral-100">
                  <span className="text-gqt-neutral-500 font-medium">Academic Verification</span>
                  <span
                    className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                      studentSelfData.academic_verification_status === 'VERIFIED'
                        ? 'bg-green-100 text-green-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}
                  >
                    {studentSelfData.academic_verification_status}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm py-1 border-b border-gqt-neutral-100">
                  <span className="text-gqt-neutral-500 font-medium">Step 23 Readiness Gate</span>
                  <span
                    className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                      studentSelfData.is_readiness_certified
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-rose-100 text-rose-700'
                    }`}
                  >
                    {studentSelfData.is_readiness_certified ? 'Certified' : 'Not Certified'}
                  </span>
                </div>
                <div className="pt-2">
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-gqt-neutral-600">Profile Completeness</span>
                    <span className="text-gqt-blue">{studentSelfData.profile_completeness_percentage}%</span>
                  </div>
                  <div className="w-full bg-gqt-neutral-100 h-2.5 rounded-full overflow-hidden">
                    <div
                      className="bg-gqt-blue h-full rounded-full transition-all duration-500"
                      style={{ width: `${studentSelfData.profile_completeness_percentage}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Placement Trajectory KPIs */}
            <div className="lg:col-span-2 space-y-6">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <Briefcase className="w-4 h-4 text-gqt-blue" />
                    Applications
                  </div>
                  <div className="text-2xl font-black text-gqt-navy mt-2">
                    {studentSelfData.total_applications}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <Users className="w-4 h-4 text-purple-600" />
                    Shortlists
                  </div>
                  <div className="text-2xl font-black text-gqt-navy mt-2">
                    {studentSelfData.total_shortlists}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <div className="flex items-center gap-2 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <Calendar className="w-4 h-4 text-amber-600" />
                    Interviews
                  </div>
                  <div className="text-2xl font-black text-gqt-navy mt-2">
                    {studentSelfData.total_interviews}
                  </div>
                </div>
              </div>

              {/* Placement Status & Offer Card */}
              <Card className="shadow-sm border-gqt-neutral-200">
                <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                  <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
                    <Award className="w-5 h-5 text-emerald-600" />
                    Placement & Offer Status
                  </h3>
                </CardHeader>
                <CardContent className="pt-4 space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-3.5 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-xs text-gqt-neutral-500 font-semibold uppercase">Selection Result</span>
                      <div className="mt-1">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                            studentSelfData.placement_result_status === 'SELECTED'
                              ? 'bg-green-100 text-green-800'
                              : studentSelfData.placement_result_status === 'REJECTED'
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-gqt-neutral-200 text-gqt-neutral-700'
                          }`}
                        >
                          {studentSelfData.placement_result_status || 'In Progress'}
                        </span>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-xs text-gqt-neutral-500 font-semibold uppercase">Offer Letter</span>
                      <div className="mt-1">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                            studentSelfData.offer_status === 'ACCEPTED'
                              ? 'bg-emerald-100 text-emerald-800'
                              : studentSelfData.offer_status === 'DECLINED'
                              ? 'bg-rose-100 text-rose-800'
                              : studentSelfData.has_offer
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gqt-neutral-200 text-gqt-neutral-700'
                          }`}
                        >
                          {studentSelfData.offer_status || (studentSelfData.has_offer ? 'Issued' : 'None')}
                        </span>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-xs text-gqt-neutral-500 font-semibold uppercase">Joining Status</span>
                      <div className="mt-1">
                        <span
                          className={`inline-flex px-2.5 py-1 rounded-md text-xs font-bold ${
                            studentSelfData.joining_status === 'JOINED'
                              ? 'bg-teal-100 text-teal-800'
                              : 'bg-gqt-neutral-200 text-gqt-neutral-700'
                          }`}
                        >
                          {studentSelfData.joining_status || 'Pending'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {studentSelfData.offered_ctc_lakhs && (
                    <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/10 to-teal-500/10 border border-emerald-200 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold">
                          <IndianRupee className="w-5 h-5" />
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-emerald-800 uppercase tracking-wider">Offered Annual CTC</p>
                          <p className="text-xl font-black text-emerald-900">{studentSelfData.offered_ctc_lakhs} LPA</p>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-800 text-xs flex items-center gap-2">
                    <Info className="w-4 h-4 flex-shrink-0" />
                    <span>Candidate isolation notice: You are viewing your personal placement trajectory. Institutional aggregates and batch analytics are restricted to authorized placement authorities.</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : null}
      </div>
    );
  }

  // Institutional Reports View (Staff & Auditor)
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-gqt-navy via-gqt-navy-light to-gqt-blue rounded-2xl p-8 text-white shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-white/10 text-white border border-white/20">
                <BarChart3 className="w-3.5 h-3.5" />
                Phase 11 Production Analytics
              </span>
              {isAuditor && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-gqt-navy">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Auditor Inspection Mode — Strict Read-Only
                </span>
              )}
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight">Institutional Reports & Analytics Hub</h1>
            <p className="text-gqt-neutral-200 mt-1 max-w-2xl text-sm">
              Authoritative aggregation layer across Corporate CRM, Academic Verification, Placement Lifecycles, and 10-Stage Funnel Yields.
            </p>
          </div>
          <div className="flex items-center gap-3 self-start md:self-auto">
            <Button
              variant="outline"
              onClick={fetchActiveTabReport}
              disabled={isLoading}
              className="bg-white/10 border-white/30 text-white hover:bg-white/20"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              onClick={handleExportCsv}
              disabled={isLoading || isExporting}
              className="bg-white text-gqt-navy hover:bg-gqt-neutral-100 font-bold shadow-md"
            >
              <Download className={`w-4 h-4 mr-2 ${isExporting ? 'animate-spin' : ''}`} />
              {isExporting ? 'Exporting...' : 'Export CSV (Sanitized)'}
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Navigation Tabs (5 Official Categories) */}
      <div className="flex items-center gap-2 border-b border-gqt-neutral-200 pb-px overflow-x-auto">
        <button
          onClick={() => setActiveTab('company')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'company'
              ? 'border-gqt-blue text-gqt-blue bg-gqt-blue/5 rounded-t-lg'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
          }`}
        >
          <Building2 className="w-4 h-4" />
          1. Company Reports
        </button>
        <button
          onClick={() => setActiveTab('students')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'students'
              ? 'border-gqt-blue text-gqt-blue bg-gqt-blue/5 rounded-t-lg'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
          }`}
        >
          <GraduationCap className="w-4 h-4" />
          2. Student Reports
        </button>
        <button
          onClick={() => setActiveTab('placements')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'placements'
              ? 'border-gqt-blue text-gqt-blue bg-gqt-blue/5 rounded-t-lg'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
          }`}
        >
          <Award className="w-4 h-4" />
          3. Placement Reports
        </button>
        <button
          onClick={() => setActiveTab('performance')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'performance'
              ? 'border-gqt-blue text-gqt-blue bg-gqt-blue/5 rounded-t-lg'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
          }`}
        >
          <TrendingUp className="w-4 h-4" />
          4. Performance Funnel
        </button>
        <button
          onClick={() => setActiveTab('monthly')}
          className={`flex items-center gap-2 px-5 py-3 text-sm font-bold border-b-2 transition-all whitespace-nowrap ${
            activeTab === 'monthly'
              ? 'border-gqt-blue text-gqt-blue bg-gqt-blue/5 rounded-t-lg'
              : 'border-transparent text-gqt-neutral-500 hover:text-gqt-navy'
          }`}
        >
          <Calendar className="w-4 h-4" />
          5. Monthly Statistics
        </button>
      </div>

      {/* TAB CONTENT */}

      {/* 1. COMPANY REPORTS TAB */}
      {activeTab === 'company' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm font-bold text-gqt-navy">
              <Filter className="w-4 h-4 text-gqt-blue" />
              Filters:
            </div>
            <div>
              <select
                value={companyTier}
                onChange={(e) => setCompanyTier(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="">All Tiers</option>
                <option value="TIER_1">Tier 1</option>
                <option value="TIER_2">Tier 2</option>
                <option value="TIER_3">Tier 3</option>
                <option value="EMERGING">Emerging</option>
              </select>
            </div>
            <div>
              <input
                type="text"
                placeholder="Industry Domain..."
                value={companyDomain}
                onChange={(e) => setCompanyDomain(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy placeholder-gqt-neutral-400"
              />
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gqt-neutral-500">From:</span>
              <input
                type="date"
                value={companyDateFrom}
                onChange={(e) => setCompanyDateFrom(e.target.value)}
                className="px-2 py-1 text-xs rounded border border-gqt-neutral-300"
              />
              <span className="text-gqt-neutral-500">To:</span>
              <input
                type="date"
                value={companyDateTo}
                onChange={(e) => setCompanyDateTo(e.target.value)}
                className="px-2 py-1 text-xs rounded border border-gqt-neutral-300"
              />
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 text-center text-gqt-neutral-500">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gqt-blue mb-2" />
              Loading corporate hiring analytics...
            </div>
          ) : companyData ? (
            <>
              {/* Summary KPI Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Companies</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">{companyData.summary.total_companies}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Total Drives</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">{companyData.summary.total_job_drives}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Submissions</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">{companyData.summary.total_submissions}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Interviews</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">{companyData.summary.total_interviews}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Selections</span>
                  <div className="text-2xl font-black text-emerald-700 mt-1">{companyData.summary.total_selections}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Confirmed Joined</span>
                  <div className="text-2xl font-black text-teal-700 mt-1">{companyData.summary.total_joinings}</div>
                </div>
              </div>

              {/* Rate & Rating Badges */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-bold text-blue-900 uppercase">Overall Selection Rate</p>
                    <p className="text-2xl font-black text-blue-800 mt-1">{companyData.summary.overall_selection_rate}%</p>
                  </div>
                  <Percent className="w-8 h-8 text-blue-400" />
                </div>
                <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-bold text-emerald-900 uppercase">Overall Joining Rate</p>
                    <p className="text-2xl font-black text-emerald-800 mt-1">{companyData.summary.overall_joining_rate}%</p>
                  </div>
                  <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                </div>
                <div className="p-4 rounded-xl bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 flex justify-between items-center">
                  <div>
                    <p className="text-xs font-bold text-amber-900 uppercase">Recruiter Satisfaction</p>
                    <p className="text-2xl font-black text-amber-800 mt-1">
                      {companyData.summary.average_recruiter_rating !== null
                        ? `${companyData.summary.average_recruiter_rating} / 5.0`
                        : 'No ratings yet'}
                    </p>
                  </div>
                  <Award className="w-8 h-8 text-amber-400" />
                </div>
              </div>

              {/* Top Companies Table */}
              <Card className="shadow-sm border-gqt-neutral-200">
                <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3 flex justify-between items-center">
                  <h3 className="text-base font-bold text-gqt-navy">Corporate Partner Hiring Breakdown</h3>
                  <span className="text-xs text-gqt-neutral-500 font-medium">Top {companyData.companies.length} records</span>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase tracking-wider border-b border-gqt-neutral-200">
                        <th className="py-3 px-4">Company Name</th>
                        <th className="py-3 px-3">Tier</th>
                        <th className="py-3 px-3">Domain</th>
                        <th className="py-3 px-3 text-right">Drives</th>
                        <th className="py-3 px-3 text-right">Submissions</th>
                        <th className="py-3 px-3 text-right">Interviews</th>
                        <th className="py-3 px-3 text-right">Selections</th>
                        <th className="py-3 px-3 text-right">Joined</th>
                        <th className="py-3 px-3 text-right">Avg CTC (LPA)</th>
                        <th className="py-3 px-4 text-center">Recruiter Rating</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gqt-neutral-100">
                      {companyData.companies.length === 0 ? (
                        <tr>
                          <td colSpan={10} className="py-8 text-center text-gqt-neutral-500 font-medium">
                            No company hiring records match the selected filters.
                          </td>
                        </tr>
                      ) : (
                        companyData.companies.map((c) => (
                          <tr key={c.company_id} className="hover:bg-gqt-neutral-50/80 transition-colors">
                            <td className="py-3 px-4 font-bold text-gqt-navy">{c.company_name}</td>
                            <td className="py-3 px-3">
                              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-gqt-neutral-200 text-gqt-neutral-800">
                                {c.tier}
                              </span>
                            </td>
                            <td className="py-3 px-3 text-gqt-neutral-600">{c.industry_domain || '—'}</td>
                            <td className="py-3 px-3 text-right font-semibold text-gqt-navy">{c.drives_count}</td>
                            <td className="py-3 px-3 text-right text-gqt-neutral-600">{c.submissions_count}</td>
                            <td className="py-3 px-3 text-right text-gqt-neutral-600">{c.interviews_count}</td>
                            <td className="py-3 px-3 text-right font-bold text-emerald-700">{c.selections_count}</td>
                            <td className="py-3 px-3 text-right font-bold text-teal-700">{c.joinings_count}</td>
                            <td className="py-3 px-3 text-right font-mono font-bold text-gqt-navy">
                              {c.avg_ctc_lakhs > 0 ? `${c.avg_ctc_lakhs} LPA` : '—'}
                            </td>
                            <td className="py-3 px-4 text-center">
                              {c.recruiter_satisfaction_rating !== null ? (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-100 text-amber-800 font-bold text-xs">
                                  ★ {c.recruiter_satisfaction_rating}
                                </span>
                              ) : (
                                <span className="text-gqt-neutral-400">—</span>
                              )}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 2. STUDENT REPORTS TAB */}
      {activeTab === 'students' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm font-bold text-gqt-navy">
              <Filter className="w-4 h-4 text-gqt-blue" />
              Student Filters:
            </div>
            <div>
              <input
                type="text"
                placeholder="Department (e.g. CSE)"
                value={studentDept}
                onChange={(e) => setStudentDept(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy placeholder-gqt-neutral-400"
              />
            </div>
            <div>
              <input
                type="number"
                placeholder="Passing Year"
                value={studentYear}
                onChange={(e) => setStudentYear(e.target.value)}
                className="px-3 py-1.5 text-xs rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy w-28"
              />
            </div>
            <div>
              <select
                value={studentVerified}
                onChange={(e) => setStudentVerified(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="ALL">Verification: All</option>
                <option value="TRUE">Verified Only</option>
                <option value="FALSE">Unverified Only</option>
              </select>
            </div>
            <div>
              <select
                value={studentCertified}
                onChange={(e) => setStudentCertified(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="ALL">Step 23 Gate: All</option>
                <option value="TRUE">Certified Only</option>
                <option value="FALSE">Non-Certified Only</option>
              </select>
            </div>
            <label className="flex items-center gap-2 text-xs font-semibold text-gqt-navy cursor-pointer">
              <input
                type="checkbox"
                checked={studentPlacedOnly}
                onChange={(e) => setStudentPlacedOnly(e.target.checked)}
                className="rounded border-gqt-neutral-300 text-gqt-blue"
              />
              Placed Only
            </label>
          </div>

          {isLoading ? (
            <div className="py-20 text-center text-gqt-neutral-500">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gqt-blue mb-2" />
              Loading student population metrics...
            </div>
          ) : studentData ? (
            <>
              {/* Summary KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Total Candidates</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">{studentData.summary.total_students}</div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Verified Academics</span>
                  <div className="text-2xl font-black text-emerald-700 mt-1">
                    {studentData.summary.total_verified_academics}{' '}
                    <span className="text-xs font-bold text-gqt-neutral-500">({studentData.summary.verification_rate}%)</span>
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Step 23 Certified</span>
                  <div className="text-2xl font-black text-blue-700 mt-1">
                    {studentData.summary.total_readiness_certified}{' '}
                    <span className="text-xs font-bold text-gqt-neutral-500">({studentData.summary.readiness_certified_rate}%)</span>
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Candidates Placed</span>
                  <div className="text-2xl font-black text-teal-700 mt-1">
                    {studentData.summary.total_placed}{' '}
                    <span className="text-xs font-bold text-gqt-neutral-500">({studentData.summary.placement_rate}%)</span>
                  </div>
                </div>
              </div>

              {/* Department & Passing Year Breakdown */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Department Breakdown */}
                <Card className="shadow-sm border-gqt-neutral-200">
                  <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                    <h3 className="text-base font-bold text-gqt-navy">Department-wise Breakdown</h3>
                  </CardHeader>
                  <CardContent className="p-0 overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase border-b border-gqt-neutral-200">
                          <th className="py-2.5 px-4">Department</th>
                          <th className="py-2.5 px-3 text-right">Students</th>
                          <th className="py-2.5 px-3 text-right">Verified</th>
                          <th className="py-2.5 px-3 text-right">Certified</th>
                          <th className="py-2.5 px-3 text-right">Placed</th>
                          <th className="py-2.5 px-4 text-right">Placement %</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gqt-neutral-100">
                        {studentData.department_breakdown.map((d) => (
                          <tr key={d.department} className="hover:bg-gqt-neutral-50">
                            <td className="py-2.5 px-4 font-bold text-gqt-navy">{d.department}</td>
                            <td className="py-2.5 px-3 text-right text-gqt-neutral-700">{d.total_students}</td>
                            <td className="py-2.5 px-3 text-right text-emerald-700 font-semibold">{d.verified_count}</td>
                            <td className="py-2.5 px-3 text-right text-blue-700 font-semibold">{d.certified_count}</td>
                            <td className="py-2.5 px-3 text-right text-teal-700 font-bold">{d.placed_count}</td>
                            <td className="py-2.5 px-4 text-right font-black text-gqt-navy">{d.placement_percentage}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </CardContent>
                </Card>

                {/* Passing Year Breakdown & Feedback Anonymity */}
                <div className="space-y-6">
                  <Card className="shadow-sm border-gqt-neutral-200">
                    <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                      <h3 className="text-base font-bold text-gqt-navy">Passing Year Cohort Distribution</h3>
                    </CardHeader>
                    <CardContent className="p-0 overflow-x-auto">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase border-b border-gqt-neutral-200">
                            <th className="py-2.5 px-4">Passing Year</th>
                            <th className="py-2.5 px-3 text-right">Total Students</th>
                            <th className="py-2.5 px-3 text-right">Placed</th>
                            <th className="py-2.5 px-4 text-right">Placement %</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gqt-neutral-100">
                          {studentData.year_breakdown.map((y) => (
                            <tr key={y.passing_year} className="hover:bg-gqt-neutral-50">
                              <td className="py-2.5 px-4 font-bold text-gqt-navy">{y.passing_year}</td>
                              <td className="py-2.5 px-3 text-right text-gqt-neutral-700">{y.total_students}</td>
                              <td className="py-2.5 px-3 text-right text-teal-700 font-bold">{y.placed_count}</td>
                              <td className="py-2.5 px-4 text-right font-black text-gqt-navy">{y.placement_percentage}%</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </CardContent>
                  </Card>

                  {/* Interview Difficulty Ratings (Strict Candidate Anonymity) */}
                  <Card className="shadow-sm border-gqt-neutral-200">
                    <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-2">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold text-gqt-navy">Interview Difficulty Perception</h4>
                        <span className="text-[11px] text-gqt-neutral-500 font-medium">Candidate Anonymity Preserved</span>
                      </div>
                    </CardHeader>
                    <CardContent className="p-4">
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                        {studentData.difficulty_distribution.map((df) => (
                          <div key={df.difficulty_level} className="p-2.5 rounded-lg bg-gqt-neutral-50 text-center border border-gqt-neutral-200">
                            <span className="text-[10px] font-bold text-gqt-neutral-500 uppercase">{df.difficulty_level}</span>
                            <p className="text-lg font-black text-gqt-navy mt-0.5">{df.rating_count}</p>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            </>
          ) : null}
        </div>
      )}

      {/* 3. PLACEMENT REPORTS TAB */}
      {activeTab === 'placements' && (
        <div className="space-y-6">
          {/* Filters Bar */}
          <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm font-bold text-gqt-navy">
              <Filter className="w-4 h-4 text-gqt-blue" />
              Placement Filters:
            </div>
            <div>
              <select
                value={placementStatus}
                onChange={(e) => setPlacementStatus(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="">Result Status: All</option>
                <option value="SELECTED">Selected</option>
                <option value="REJECTED">Rejected</option>
                <option value="WAITING_LIST">Waiting List</option>
                <option value="HOLD">On Hold</option>
              </select>
            </div>
            <div>
              <select
                value={offerStatus}
                onChange={(e) => setOfferStatus(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="">Offer Status: All</option>
                <option value="ACCEPTED">Accepted</option>
                <option value="DECLINED">Declined</option>
                <option value="PENDING_RESPONSE">Pending Response</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>
            <div>
              <select
                value={joiningStatus}
                onChange={(e) => setJoiningStatus(e.target.value)}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value="">Joining Status: All</option>
                <option value="JOINED">Joined</option>
                <option value="NOT_JOINED">Not Joined</option>
                <option value="DEFERRED">Deferred</option>
                <option value="PENDING_JOINING">Pending Joining</option>
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 text-center text-gqt-neutral-500">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gqt-blue mb-2" />
              Loading Step 36–41 placement lifecycle records...
            </div>
          ) : placementData ? (
            <>
              {/* Step 36-41 Life-Cycle Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Final Result Card */}
                <Card className="shadow-sm border-gqt-neutral-200">
                  <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-2">
                    <h4 className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Step 36: Final Result Status</h4>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-emerald-700 font-bold">Selected</span>
                      <span className="font-black text-gqt-navy">{placementData.summary.total_selected}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-rose-700 font-semibold">Rejected</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.total_rejected}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-amber-700 font-semibold">Waiting List</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.total_waiting_list}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-blue-700 font-semibold">Hold</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.total_hold}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Offer Letter Lifecycle Card */}
                <Card className="shadow-sm border-gqt-neutral-200">
                  <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-2">
                    <h4 className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Step 38: Offer Letter Lifecycle</h4>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-emerald-700 font-bold">Accepted</span>
                      <span className="font-black text-emerald-800">{placementData.summary.offers_accepted}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-rose-700 font-semibold">Declined</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.offers_declined}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-blue-700 font-semibold">Pending Response</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.offers_pending}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gqt-neutral-500 font-semibold">Expired</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.offers_expired}</span>
                    </div>
                  </CardContent>
                </Card>

                {/* Joining Outcome Card */}
                <Card className="shadow-sm border-gqt-neutral-200">
                  <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-2">
                    <h4 className="text-xs font-bold text-gqt-navy uppercase tracking-wider">Step 40: Joining Outcomes</h4>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-teal-700 font-bold">Confirmed Joined</span>
                      <span className="font-black text-teal-800">{placementData.summary.joining_joined}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-rose-700 font-semibold">Not Joined</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.joining_not_joined}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-amber-700 font-semibold">Deferred</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.joining_deferred}</span>
                    </div>
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-blue-700 font-semibold">Pending Joining</span>
                      <span className="font-semibold text-gqt-neutral-700">{placementData.summary.joining_pending}</span>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Compensation Metrics Card */}
              <div className="p-5 rounded-2xl bg-gradient-to-r from-emerald-600 to-teal-700 text-white shadow-lg">
                <div className="flex items-center gap-2 mb-3">
                  <IndianRupee className="w-5 h-5" />
                  <h4 className="text-sm font-bold uppercase tracking-wider">Institutional Compensation Analytics (CTC in ₹ Lakhs)</h4>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur border border-white/20">
                    <span className="text-xs text-white/80 font-medium">Minimum CTC</span>
                    <p className="text-2xl font-black mt-1">{placementData.summary.min_ctc_lakhs} LPA</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur border border-white/20">
                    <span className="text-xs text-white/80 font-medium">Maximum CTC</span>
                    <p className="text-2xl font-black mt-1">{placementData.summary.max_ctc_lakhs} LPA</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur border border-white/20">
                    <span className="text-xs text-white/80 font-medium">Average CTC</span>
                    <p className="text-2xl font-black mt-1">{placementData.summary.avg_ctc_lakhs} LPA</p>
                  </div>
                  <div className="p-3 rounded-xl bg-white/10 backdrop-blur border border-white/20">
                    <span className="text-xs text-white/80 font-medium">Median CTC</span>
                    <p className="text-2xl font-black mt-1">{placementData.summary.median_ctc_lakhs} LPA</p>
                  </div>
                </div>
              </div>

              {/* Company Placements Table */}
              <Card className="shadow-sm border-gqt-neutral-200">
                <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                  <h3 className="text-base font-bold text-gqt-navy">Company Placements Table</h3>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase border-b border-gqt-neutral-200">
                        <th className="py-2.5 px-4">Company Name</th>
                        <th className="py-2.5 px-3 text-right">Selected Candidates</th>
                        <th className="py-2.5 px-3 text-right">Offers Accepted</th>
                        <th className="py-2.5 px-3 text-right">Confirmed Joined</th>
                        <th className="py-2.5 px-4 text-right">Average CTC (LPA)</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gqt-neutral-100">
                      {placementData.company_placements.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-6 text-center text-gqt-neutral-500 font-medium">
                            No placement records found.
                          </td>
                        </tr>
                      ) : (
                        placementData.company_placements.map((cp) => (
                          <tr key={cp.company_name} className="hover:bg-gqt-neutral-50">
                            <td className="py-2.5 px-4 font-bold text-gqt-navy">{cp.company_name}</td>
                            <td className="py-2.5 px-3 text-right text-emerald-700 font-bold">{cp.total_selected}</td>
                            <td className="py-2.5 px-3 text-right text-teal-700 font-semibold">{cp.offers_accepted}</td>
                            <td className="py-2.5 px-3 text-right text-gqt-navy font-black">{cp.confirmed_joined}</td>
                            <td className="py-2.5 px-4 text-right font-mono font-bold text-gqt-navy">
                              {cp.average_ctc_lakhs > 0 ? `${cp.average_ctc_lakhs} LPA` : '—'}
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 4. PERFORMANCE FUNNEL TAB */}
      {activeTab === 'performance' && (
        <div className="space-y-6">
          {isLoading ? (
            <div className="py-20 text-center text-gqt-neutral-500">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gqt-blue mb-2" />
              Computing 10-stage recruitment conversion funnel...
            </div>
          ) : performanceData ? (
            <>
              {/* Funnel Pipeline Yield Card */}
              <div className="p-6 rounded-2xl bg-gradient-to-r from-gqt-navy to-gqt-blue text-white shadow-xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div>
                  <span className="text-xs font-bold text-blue-200 uppercase tracking-wider">Overall Pipeline Yield</span>
                  <div className="text-3xl font-black mt-1">
                    {performanceData.funnel.overall_pipeline_yield}%{' '}
                    <span className="text-sm font-normal text-blue-100">
                      ({performanceData.funnel.total_joined} Joined / {performanceData.funnel.total_applications} Applications)
                    </span>
                  </div>
                  <p className="text-xs text-blue-200 mt-1 max-w-xl">
                    Represents the end-to-end recruitment efficiency from candidate applications through Stage 10 confirmed joining.
                  </p>
                </div>
              </div>

              {/* 10-Stage Funnel Table and Progression */}
              <Card className="shadow-sm border-gqt-neutral-200">
                <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                  <h3 className="text-base font-bold text-gqt-navy">
                    Objective 10-Stage Recruitment Conversion Funnel
                  </h3>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase border-b border-gqt-neutral-200">
                        <th className="py-3 px-4 w-12 text-center">Stage</th>
                        <th className="py-3 px-4">Stage Name</th>
                        <th className="py-3 px-4 text-right">Candidate Count</th>
                        <th className="py-3 px-4 text-right">Stage-over-Stage Conversion</th>
                        <th className="py-3 px-4 text-right">Overall Conversion</th>
                        <th className="py-3 px-6 w-48">Retention Bar</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gqt-neutral-100">
                      {performanceData.funnel.stages.map((stg) => (
                        <tr key={stg.stage_number} className="hover:bg-gqt-neutral-50 transition-colors">
                          <td className="py-3 px-4 text-center">
                            <span className="w-6 h-6 rounded-full bg-gqt-blue/10 text-gqt-blue inline-flex items-center justify-center font-bold text-xs">
                              {stg.stage_number}
                            </span>
                          </td>
                          <td className="py-3 px-4 font-bold text-gqt-navy">{stg.stage_name}</td>
                          <td className="py-3 px-4 text-right font-black text-gqt-navy text-sm">{stg.count}</td>
                          <td className="py-3 px-4 text-right font-semibold text-emerald-700">
                            {stg.conversion_rate_from_prev}%
                          </td>
                          <td className="py-3 px-4 text-right font-bold text-gqt-blue">
                            {stg.overall_conversion_rate}%
                          </td>
                          <td className="py-3 px-6">
                            <div className="w-full bg-gqt-neutral-100 h-2.5 rounded-full overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-gqt-blue to-teal-500 h-full rounded-full transition-all duration-300"
                                style={{ width: `${Math.min(100, Math.max(0, stg.overall_conversion_rate))}%` }}
                              />
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      )}

      {/* 5. MONTHLY STATISTICS TAB */}
      {activeTab === 'monthly' && (
        <div className="space-y-6">
          {/* Year & Month Selector */}
          <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 text-sm font-bold text-gqt-navy">
              <Calendar className="w-4 h-4 text-gqt-blue" />
              Month Period:
            </div>
            <div>
              <select
                value={selectedYear}
                onChange={(e) => setSelectedYear(parseInt(e.target.value, 10))}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                <option value={2024}>2024</option>
                <option value={2025}>2025</option>
                <option value={2026}>2026</option>
                <option value={2027}>2027</option>
              </select>
            </div>
            <div>
              <select
                value={selectedMonth}
                onChange={(e) => setSelectedMonth(parseInt(e.target.value, 10))}
                className="px-3 py-1.5 text-xs font-semibold rounded-lg border border-gqt-neutral-300 bg-white text-gqt-navy"
              >
                {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                  <option key={m} value={m}>
                    {new Date(2000, m - 1).toLocaleString('default', { month: 'long' })}
                  </option>
                ))}
              </select>
            </div>
            <div className="text-xs text-gqt-neutral-500 ml-auto flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              Deterministic Timezone: <span className="font-semibold text-gqt-navy">Asia/Kolkata</span>
            </div>
          </div>

          {isLoading ? (
            <div className="py-20 text-center text-gqt-neutral-500">
              <RefreshCw className="w-8 h-8 animate-spin mx-auto text-gqt-blue mb-2" />
              Aggregating monthly recruitment statistics...
            </div>
          ) : monthlyData ? (
            <>
              {/* Monthly Activity Breakdown Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Drives Posted</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">
                    {monthlyData.metrics.job_drives_posted}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Submissions</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">
                    {monthlyData.metrics.submissions_dispatched}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Interviews Conducted</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">
                    {monthlyData.metrics.interviews_conducted}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Results Received</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">
                    {monthlyData.metrics.results_received}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Selections Confirmed</span>
                  <div className="text-2xl font-black text-emerald-700 mt-1">
                    {monthlyData.metrics.candidates_selected}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Offers Accepted</span>
                  <div className="text-2xl font-black text-teal-700 mt-1">
                    {monthlyData.metrics.offers_accepted}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Confirmed Joined</span>
                  <div className="text-2xl font-black text-blue-700 mt-1">
                    {monthlyData.metrics.joinings_confirmed}
                  </div>
                </div>
                <div className="p-4 rounded-xl bg-white border border-gqt-neutral-200 shadow-sm">
                  <span className="text-xs font-semibold text-gqt-neutral-500 uppercase">Total CTC Offered</span>
                  <div className="text-2xl font-black text-gqt-navy mt-1">
                    ₹{monthlyData.metrics.total_ctc_offered_lakhs}L
                  </div>
                </div>
              </div>

              {/* 12-Month Annual Trend Table */}
              <Card className="shadow-sm border-gqt-neutral-200">
                <CardHeader className="bg-gqt-neutral-50/70 border-b border-gqt-neutral-200 pb-3">
                  <h3 className="text-base font-bold text-gqt-navy">
                    {monthlyData.year} Annual 12-Month Progression Trend
                  </h3>
                </CardHeader>
                <CardContent className="p-0 overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-gqt-neutral-100 text-gqt-neutral-700 font-bold uppercase border-b border-gqt-neutral-200">
                        <th className="py-2.5 px-4">Month</th>
                        <th className="py-2.5 px-3 text-right">Drives Posted</th>
                        <th className="py-2.5 px-3 text-right">Selected Candidates</th>
                        <th className="py-2.5 px-3 text-right">Offers Accepted</th>
                        <th className="py-2.5 px-4 text-right">Joinings Confirmed</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gqt-neutral-100">
                      {monthlyData.annual_trend.map((tr) => (
                        <tr
                          key={tr.month}
                          className={`hover:bg-gqt-neutral-50 ${
                            tr.month === monthlyData.month ? 'bg-gqt-blue/5 font-semibold' : ''
                          }`}
                        >
                          <td className="py-2.5 px-4 font-bold text-gqt-navy">
                            {new Date(2000, tr.month - 1).toLocaleString('default', { month: 'long' })}
                            {tr.month === monthlyData.month && (
                              <span className="ml-2 px-2 py-0.5 rounded text-[10px] bg-gqt-blue text-white">Active</span>
                            )}
                          </td>
                          <td className="py-2.5 px-3 text-right text-gqt-neutral-700">{tr.job_drives_posted}</td>
                          <td className="py-2.5 px-3 text-right text-emerald-700 font-bold">{tr.candidates_selected}</td>
                          <td className="py-2.5 px-3 text-right text-teal-700 font-bold">{tr.offers_accepted}</td>
                          <td className="py-2.5 px-4 text-right text-blue-700 font-black">{tr.joinings_confirmed}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </CardContent>
              </Card>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
};
