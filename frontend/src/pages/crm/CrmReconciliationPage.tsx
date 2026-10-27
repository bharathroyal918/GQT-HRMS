import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Building2,
  Calendar,
  CheckCircle2,
  Database,
  FileText,
  GraduationCap,
  History,
  Lock,
  MessageSquare,
  Play,
  RefreshCw,
  Send,
  ShieldAlert,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { crmApi } from '../../api/crmApi';
import { useAuth } from '../../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/common/Card';
import { Button } from '../../components/common/Button';
import { StatusBadge } from '../../components/common/StatusBadge';
import { LoadingState } from '../../components/common/LoadingState';
import { ErrorState } from '../../components/common/ErrorState';
import { CRMConflictSeverity } from '../../types/crmIntegration';

export const CrmReconciliationPage: React.FC = () => {
  const queryClient = useQueryClient();
  const { hasRole, hasAnyRole } = useAuth();

  const [isSyncModalOpen, setIsSyncModalOpen] = useState(false);
  const [isDryRun, setIsDryRun] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<'ALL' | CRMConflictSeverity>('ALL');
  const [areaFilter, setAreaFilter] = useState<string>('ALL');

  // RBAC checks: Auditor is strictly read-only; staff can run sync
  const isAuditor = hasRole('AUDITOR') && !hasRole('ADMIN');
  const canRunReconciliation =
    hasAnyRole(['ADMIN', 'PLACEMENT_HEAD', 'PLACEMENT_OFFICER', 'HR_RELATIONSHIP_MGR']) && !isAuditor;

  // Diagnostics query
  const {
    data: diagnosticsResponse,
    isLoading: isDiagnosticsLoading,
    isFetching: isDiagnosticsFetching,
    error: diagnosticsError,
    refetch: refetchDiagnostics,
  } = useQuery({
    queryKey: ['crm-reconciliation-diagnostics'],
    queryFn: () => crmApi.getReconciliationDiagnostics(),
  });

  // Reconciliation runs history query
  const {
    data: historyResponse,
    isLoading: isHistoryLoading,
    refetch: refetchHistory,
  } = useQuery({
    queryKey: ['crm-reconciliation-history'],
    queryFn: () => crmApi.getReconciliationHistory(),
  });

  // Reconciliation mutation
  const syncMutation = useMutation({
    mutationFn: (dryRun: boolean) => crmApi.runReconciliationSync(dryRun),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-reconciliation-diagnostics'] });
      queryClient.invalidateQueries({ queryKey: ['crm-reconciliation-history'] });
      queryClient.invalidateQueries({ queryKey: ['companies'] });
      setIsSyncModalOpen(false);
    },
  });

  if (isDiagnosticsLoading && !diagnosticsResponse) {
    return (
      <div className="py-12">
        <LoadingState message="Scanning 8 domain areas for cross-module database integrity..." />
      </div>
    );
  }

  if (diagnosticsError || !diagnosticsResponse?.success) {
    return (
      <div className="py-8">
        <ErrorState
          title="Diagnostic Audit Scan Failed"
          message={diagnosticsError instanceof Error ? diagnosticsError.message : 'Failed to query CRM database health.'}
          onRetry={() => refetchDiagnostics()}
        />
      </div>
    );
  }

  const diagnostics = diagnosticsResponse.data;
  const summary = diagnostics.summary;
  const areas = diagnostics.areas;
  const conflicts = diagnostics.conflicts || [];

  // Filter conflicts
  const filteredConflicts = conflicts.filter((c) => {
    const matchesSeverity = severityFilter === 'ALL' || c.severity === severityFilter;
    const matchesArea = areaFilter === 'ALL' || c.area.toLowerCase().includes(areaFilter.toLowerCase());
    return matchesSeverity && matchesArea;
  });

  // Area icons mapping
  const areaIcons: Record<string, React.ElementType> = {
    company: Building2,
    hr: Users,
    students: GraduationCap,
    resumes: FileText,
    interviews: Calendar,
    placements: ShieldCheck,
    feedback: MessageSquare,
    communications: Send,
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-gqt-neutral-200 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gqt-navy tracking-tight">
              CRM Database Reconciliation
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-blue-50 text-gqt-blue border border-blue-200">
              Phase 10 Engine
            </span>
          </div>
          <p className="text-sm text-gqt-neutral-600 mt-1">
            8-Area cross-module consistency validation, safe non-destructive reconciliation, and audit verification.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            leftIcon={<RefreshCw className={`w-4 h-4 ${isDiagnosticsFetching ? 'animate-spin' : ''}`} />}
            onClick={() => refetchDiagnostics()}
            disabled={isDiagnosticsFetching}
          >
            {isDiagnosticsFetching ? 'Scanning...' : 'Run Diagnostic Scan'}
          </Button>

          {canRunReconciliation ? (
            <Button
              size="sm"
              variant="primary"
              leftIcon={<Play className="w-4 h-4" />}
              onClick={() => {
                setIsDryRun(false);
                setIsSyncModalOpen(true);
              }}
            >
              Reconcile Database
            </Button>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gqt-neutral-100 text-xs font-semibold text-gqt-neutral-600 border border-gqt-neutral-200">
              <Lock className="w-3.5 h-3.5 text-gqt-neutral-500" />
              Auditor Read-Only
            </div>
          )}
        </div>
      </div>

      {/* Auditor Notice Banner */}
      {isAuditor && (
        <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900">
            <span className="font-bold">Auditor Role Active:</span> You have full read-only inspection access across all 8 domain diagnostic areas, integrity scans, and reconciliation logs. Mutating database sync operations are restricted to placement operations staff.
          </div>
        </div>
      )}

      {/* Platform Health Score Banner Card */}
      <Card elevation="sm" className="p-6 border-l-4 border-l-gqt-navy">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-gqt-navy">Cross-Module Platform Health Score</h2>
              <StatusBadge
                variant={
                  summary.status === 'HEALTHY'
                    ? 'success'
                    : summary.status === 'NEEDS_ATTENTION'
                    ? 'warning'
                    : 'danger'
                }
                label={summary.status.replace(/_/g, ' ')}
              />
            </div>
            <p className="text-xs text-gqt-neutral-600">
              Diagnostic audit computed across Company, HR, Student, Resume, Interview, Placement, Feedback, and Communication records.
            </p>
            <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-gqt-neutral-600 pt-1">
              <span>
                Total Records Checked: <strong className="text-gqt-navy">{summary.total_records_checked.toLocaleString()}</strong>
              </span>
              <span>•</span>
              <span>
                Consistent Records: <strong className="text-emerald-700">{summary.total_consistent_records.toLocaleString()}</strong>
              </span>
              <span>•</span>
              <span>
                Conflicts Detected: <strong className={summary.total_conflicts > 0 ? 'text-amber-600' : 'text-emerald-700'}>{summary.total_conflicts}</strong>
              </span>
              <span>•</span>
              <span>
                As of: <span className="text-gqt-neutral-500">{new Date(summary.as_of).toLocaleTimeString()}</span>
              </span>
            </div>
          </div>

          {/* Health Score Gauge */}
          <div className="flex flex-col items-center justify-center p-4 rounded-xl bg-gqt-neutral-50 border border-gqt-neutral-200 min-w-[180px]">
            <span className="text-4xl font-extrabold tracking-tight text-gqt-navy">
              {summary.health_score_percentage}%
            </span>
            <div className="w-full bg-gqt-neutral-200 rounded-full h-2 mt-2 overflow-hidden">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${
                  summary.health_score_percentage >= 95
                    ? 'bg-emerald-500'
                    : summary.health_score_percentage >= 80
                    ? 'bg-amber-500'
                    : 'bg-rose-500'
                }`}
                style={{ width: `${Math.max(5, summary.health_score_percentage)}%` }}
              />
            </div>
            <span className="text-[11px] font-semibold text-gqt-neutral-500 mt-1 uppercase tracking-wider">
              Integrity Index
            </span>
          </div>
        </div>
      </Card>

      {/* 8 Domain Areas Health Cards Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-base font-bold text-gqt-navy">
            8 Domain Integration Diagnostic Areas
          </h3>
          <span className="text-xs text-gqt-neutral-500">
            Per HRMS Recruitment Workflow Specification
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(areas).map(([areaKey, areaData]) => {
            const Icon = areaIcons[areaKey] || Database;
            const isClean = areaData.conflicts === 0;
            const isCritical = areaData.status === 'CRITICAL';

            return (
              <Card
                key={areaKey}
                elevation="sm"
                className={`p-4 transition-all duration-200 hover:border-gqt-neutral-300 border-t-4 ${
                  isClean
                    ? 'border-t-emerald-500'
                    : isCritical
                    ? 'border-t-rose-500'
                    : 'border-t-amber-500'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="p-2 rounded-lg bg-gqt-neutral-100 text-gqt-navy">
                    <Icon className="w-4 h-4" />
                  </div>
                  <StatusBadge
                    variant={isClean ? 'success' : isCritical ? 'danger' : 'warning'}
                    label={areaData.status}
                    showDot={!isClean}
                  />
                </div>

                <div className="mt-3">
                  <h4 className="text-sm font-bold text-gqt-navy truncate">{areaData.name}</h4>
                  <div className="flex items-baseline justify-between mt-1 text-xs">
                    <span className="text-gqt-neutral-500">Consistent Records</span>
                    <span className="font-bold text-gqt-charcoal">
                      {areaData.consistent} / {areaData.total}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between mt-0.5 text-xs">
                    <span className="text-gqt-neutral-500">Conflicts Found</span>
                    <span
                      className={`font-bold ${
                        areaData.conflicts > 0 ? 'text-rose-600' : 'text-emerald-600'
                      }`}
                    >
                      {areaData.conflicts}
                    </span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Cross-Module Conflicts Table */}
      <Card elevation="sm">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <CardTitle>Cross-Module Data Conflicts & Integrity Issues</CardTitle>
            <p className="text-xs text-gqt-neutral-500 mt-0.5">
              Identified integrity violations requiring automatic reconciliation or manual attention.
            </p>
          </div>

          {/* Conflict Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={areaFilter}
              onChange={(e) => setAreaFilter(e.target.value)}
              className="rounded-md border border-gqt-neutral-300 bg-white px-2.5 py-1 text-xs font-semibold text-gqt-neutral-700"
            >
              <option value="ALL">All Domain Areas</option>
              <option value="Company">Company</option>
              <option value="HR Contacts">HR Contacts</option>
              <option value="Students">Students</option>
              <option value="Resume Versions">Resume Versions</option>
              <option value="Interview Status">Interview Status</option>
              <option value="Placement Status">Placement Status</option>
              <option value="Feedback">Feedback</option>
              <option value="Communication History">Communication History</option>
            </select>
            <div className="flex items-center gap-1 bg-gqt-neutral-100 p-1 rounded-lg text-xs">
              {(['ALL', 'CRITICAL', 'WARNING', 'INFO'] as const).map((sev) => (
                <button
                  key={sev}
                  onClick={() => setSeverityFilter(sev)}
                  className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                    severityFilter === sev
                      ? 'bg-white text-gqt-navy shadow-sm'
                      : 'text-gqt-neutral-600 hover:text-gqt-navy'
                  }`}
                >
                  {sev}
                </button>
              ))}
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {filteredConflicts.length === 0 ? (
            <div className="p-10 text-center space-y-2">
              <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
              <h4 className="text-sm font-bold text-gqt-navy">Zero Cross-Module Conflicts Detected</h4>
              <p className="text-xs text-gqt-neutral-500 max-w-md mx-auto">
                All 8 domain areas (Companies, HR Contacts, Candidates, Resumes, Interviews, Placements, Feedback, and Timelines) are fully consistent with zero orphaned or conflicting records.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Severity</th>
                    <th className="py-3 px-4">Domain Area</th>
                    <th className="py-3 px-4">Resource</th>
                    <th className="py-3 px-4">Conflict Description</th>
                    <th className="py-3 px-4">Recommended Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {filteredConflicts.map((c, idx) => (
                    <tr key={idx} className="hover:bg-gqt-neutral-50/60 transition-colors">
                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={
                            c.severity === 'CRITICAL'
                              ? 'danger'
                              : c.severity === 'WARNING'
                              ? 'warning'
                              : 'info'
                          }
                          label={c.severity}
                        />
                      </td>
                      <td className="py-3 px-4 font-semibold text-gqt-navy">{c.area}</td>
                      <td className="py-3 px-4 font-mono text-[11px] text-gqt-neutral-600">
                        {c.resource_type}: {c.resource_id.substring(0, 8)}...
                      </td>
                      <td className="py-3 px-4 text-gqt-charcoal max-w-xs">{c.description}</td>
                      <td className="py-3 px-4 text-gqt-neutral-600 max-w-xs italic">
                        {c.recommended_action}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Reconciliation Audit Runs */}
      <Card elevation="sm">
        <CardHeader className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <History className="w-4 h-4 text-gqt-blue" />
              Reconciliation Execution Audit Log
            </CardTitle>
            <p className="text-xs text-gqt-neutral-500 mt-0.5">
              Tamper-evident log of all reconciliation scans and sync operations recorded in database.
            </p>
          </div>
          <Button
            size="sm"
            variant="ghost"
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            onClick={() => refetchHistory()}
          >
            Refresh History
          </Button>
        </CardHeader>

        <CardContent className="p-0">
          {isHistoryLoading ? (
            <div className="py-8">
              <LoadingState message="Loading reconciliation audit history..." />
            </div>
          ) : !historyResponse?.data || historyResponse.data.length === 0 ? (
            <div className="p-8 text-center text-xs text-gqt-neutral-500">
              No previous reconciliation runs recorded. Trigger a reconciliation run to establish baseline.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-gqt-neutral-50 border-b border-gqt-neutral-200 text-gqt-neutral-600 font-bold uppercase tracking-wider">
                  <tr>
                    <th className="py-3 px-4">Run Timestamp</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Triggered By</th>
                    <th className="py-3 px-4">Records Checked</th>
                    <th className="py-3 px-4">Conflicts</th>
                    <th className="py-3 px-4">Synchronized</th>
                    <th className="py-3 px-4">Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {historyResponse.data.map((run) => (
                    <tr key={run.id} className="hover:bg-gqt-neutral-50/60 transition-colors">
                      <td className="py-3 px-4 font-mono text-[11px] text-gqt-charcoal">
                        {new Date(run.created_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={
                            run.status === 'COMPLETED'
                              ? 'success'
                              : run.status === 'IN_PROGRESS'
                              ? 'warning'
                              : 'danger'
                          }
                          label={run.status}
                        />
                      </td>
                      <td className="py-3 px-4 text-gqt-charcoal">
                        {run.triggered_by_name || 'System / Auto'}
                      </td>
                      <td className="py-3 px-4 text-gqt-navy font-semibold">
                        {run.total_records_checked}
                      </td>
                      <td className="py-3 px-4 text-amber-600 font-semibold">
                        {run.conflicts_detected}
                      </td>
                      <td className="py-3 px-4 text-emerald-600 font-semibold">
                        {run.records_synchronized}
                      </td>
                      <td className="py-3 px-4 text-gqt-neutral-600 max-w-sm truncate" title={run.summary}>
                        {run.summary}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reconciliation Trigger Modal */}
      {isSyncModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full overflow-hidden border border-gqt-neutral-200">
            <div className="p-5 border-b border-gqt-neutral-100 flex items-center justify-between">
              <h3 className="text-base font-bold text-gqt-navy flex items-center gap-2">
                <Database className="w-5 h-5 text-gqt-blue" />
                Trigger CRM Database Reconciliation
              </h3>
              <button
                onClick={() => setIsSyncModalOpen(false)}
                className="text-gqt-neutral-400 hover:text-gqt-navy text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="p-5 space-y-4 text-xs text-gqt-charcoal">
              <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 text-blue-900 space-y-1">
                <p className="font-bold">What this reconciliation operation does:</p>
                <ul className="list-disc list-inside space-y-0.5 text-blue-800">
                  <li>Promotes placement partner companies to <strong>ACTIVE_HIRING_PARTNER</strong> status.</li>
                  <li>Generates an immutable audit snapshot in the reconciliation history table.</li>
                  <li>Ensures zero shadow tables and zero silent deletion of conflicting records.</li>
                </ul>
              </div>

              {/* Dry-run toggle */}
              <label className="flex items-start gap-2.5 p-3 rounded-lg border border-gqt-neutral-200 bg-gqt-neutral-50 hover:bg-gqt-neutral-100/50 cursor-pointer transition-colors">
                <input
                  type="checkbox"
                  checked={isDryRun}
                  onChange={(e) => setIsDryRun(e.target.checked)}
                  className="mt-0.5 rounded text-gqt-blue focus:ring-gqt-blue"
                />
                <div>
                  <span className="font-bold text-gqt-navy">Dry-Run Simulation Mode</span>
                  <p className="text-gqt-neutral-500 text-[11px] mt-0.5">
                    If checked, analyzes cross-module data and simulates promotion without writing changes to the database.
                  </p>
                </div>
              </label>

              {syncMutation.isError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-700">
                  {syncMutation.error instanceof Error ? syncMutation.error.message : 'Reconciliation failed.'}
                </div>
              )}
            </div>

            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-100 flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsSyncModalOpen(false)}
                disabled={syncMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                leftIcon={<Play className="w-3.5 h-3.5" />}
                onClick={() => syncMutation.mutate(isDryRun)}
                disabled={syncMutation.isPending}
              >
                {syncMutation.isPending
                  ? 'Reconciling...'
                  : isDryRun
                  ? 'Run Simulation (Dry-Run)'
                  : 'Execute Live Reconciliation'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
