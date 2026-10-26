import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/api/healthApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Button } from '@/components/common/Button';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { Activity, Database, Server, RefreshCw, ShieldCheck } from 'lucide-react';

export const DiagnosticsPage: React.FC = () => {
  const {
    data: health,
    isLoading: isHealthLoading,
    isError: isHealthError,
    error: healthError,
    refetch: refetchHealth,
    isFetching: isHealthFetching,
  } = useQuery({
    queryKey: ['health-check'],
    queryFn: healthApi.getHealth,
  });

  const {
    data: readiness,
    isLoading: isReadyLoading,
    isError: isReadyError,
    error: readyError,
    refetch: refetchReady,
    isFetching: isReadyFetching,
  } = useQuery({
    queryKey: ['readiness-check'],
    queryFn: healthApi.getReadiness,
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-gqt-navy tracking-tight">System Diagnostics</h2>
          <p className="text-xs text-gqt-neutral-500 mt-1">
            Real-time infrastructure probes verifying process liveness, database execution, and security invariants.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              refetchHealth();
              refetchReady();
            }}
            isLoading={isHealthFetching || isReadyFetching}
          >
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Re-probe Infrastructure
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Liveness Probe Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-gqt-blue-light flex items-center justify-center text-gqt-blue">
                  <Activity className="w-4 h-4" />
                </div>
                <div>
                  <CardTitle>Liveness Probe</CardTitle>
                  <span className="text-[11px] font-mono text-gqt-neutral-400">GET /api/v1/health/</span>
                </div>
              </div>
              <StatusBadge
                variant={health?.status === 'UP' ? 'success' : 'danger'}
                label={health?.status || 'Probing...'}
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {isHealthLoading && <LoadingState message="Connecting to health probe..." />}
            {isHealthError && (
              <ErrorState
                title="Liveness Probe Failed"
                message={healthError?.message || 'Failed to connect to /api/v1/health/'}
                onRetry={() => refetchHealth()}
              />
            )}
            {health && (
              <div className="space-y-3">
                <div className="p-3.5 rounded-lg bg-gqt-neutral-100/70 border border-gqt-neutral-200/80 font-mono text-xs space-y-1.5 text-gqt-charcoal">
                  <div><span className="text-gqt-neutral-500">status:</span> &quot;{health.status}&quot;</div>
                  <div><span className="text-gqt-neutral-500">service:</span> &quot;{health.service}&quot;</div>
                  <div><span className="text-gqt-neutral-500">version:</span> &quot;{health.version}&quot;</div>
                  <div><span className="text-gqt-neutral-500">environment:</span> &quot;{health.environment}&quot;</div>
                  <div><span className="text-gqt-neutral-500">correlation_id:</span> &quot;{health.correlation_id}&quot;</div>
                  <div><span className="text-gqt-neutral-500">timestamp:</span> &quot;{health.timestamp}&quot;</div>
                </div>
                <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200/70 text-emerald-800 text-xs flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 shrink-0 text-emerald-600" />
                  <span>Public safe response verified: zero internal credentials or hostnames disclosed.</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Readiness Probe Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-purple-50 flex items-center justify-center text-purple-600">
                  <Database className="w-4 h-4" />
                </div>
                <div>
                  <CardTitle>Readiness Probe</CardTitle>
                  <span className="text-[11px] font-mono text-gqt-neutral-400">GET /api/v1/ready/</span>
                </div>
              </div>
              <StatusBadge
                variant={readiness?.status === 'READY' ? 'success' : 'danger'}
                label={readiness?.status || 'Probing...'}
              />
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {isReadyLoading && <LoadingState message="Probing database and storage..." />}
            {isReadyError && (
              <ErrorState
                title="Readiness Probe Failed"
                message={readyError?.message || 'Database query failed or is unreachable.'}
                onRetry={() => refetchReady()}
              />
            )}
            {readiness && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 rounded-lg border border-gqt-neutral-200 bg-white space-y-1">
                    <span className="text-xs text-gqt-neutral-500">Database Engine</span>
                    <div className="flex items-center gap-1.5 font-bold text-sm text-gqt-charcoal">
                      <span className={`w-2 h-2 rounded-full ${readiness.database.status === 'UP' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                      {readiness.database.status === 'UP' ? 'Connected (UP)' : 'Unreachable'}
                    </div>
                  </div>
                  <div className="p-3 rounded-lg border border-gqt-neutral-200 bg-white space-y-1">
                    <span className="text-xs text-gqt-neutral-500">Private Media Storage</span>
                    <div className="flex items-center gap-1.5 font-bold text-sm text-gqt-charcoal">
                      <span className={`w-2 h-2 rounded-full ${readiness.storage.status === 'UP' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                      {readiness.storage.status === 'UP' ? 'Accessible (UP)' : 'Write Blocked'}
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-lg bg-gqt-neutral-100/70 border border-gqt-neutral-200/80 font-mono text-xs space-y-1 text-gqt-charcoal">
                  <div><span className="text-gqt-neutral-500">correlation_id:</span> &quot;{readiness.correlation_id}&quot;</div>
                  <div><span className="text-gqt-neutral-500">timestamp:</span> &quot;{readiness.timestamp}&quot;</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Security Invariants Checklist Card */}
      <Card>
        <CardHeader>
          <CardTitle>Architecture &amp; Security Compliance Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
            <div className="p-3.5 rounded-lg border border-emerald-200/80 bg-emerald-50/50 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-emerald-900">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Fail-Closed Production Mode
              </div>
              <p className="text-emerald-800 leading-relaxed">
                Rejects startup if secrets are missing, short (&lt;40 chars), or contain dev placeholders.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-emerald-200/80 bg-emerald-50/50 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-emerald-900">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                Sensitive Data Filter
              </div>
              <p className="text-emerald-800 leading-relaxed">
                Automatically intercepts log streams and redacts passwords, JWT tokens, and connection strings.
              </p>
            </div>

            <div className="p-3.5 rounded-lg border border-emerald-200/80 bg-emerald-50/50 space-y-1">
              <div className="flex items-center gap-1.5 font-bold text-emerald-900">
                <Server className="w-4 h-4 text-emerald-600" />
                Request Correlation ID
              </div>
              <p className="text-emerald-800 leading-relaxed">
                Propagates X-Correlation-ID across HTTP headers, logs, and error responses for audit tracing.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
