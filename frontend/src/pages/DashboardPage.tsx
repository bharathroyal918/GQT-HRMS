import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/api/healthApi';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/common/Card';
import { StatusBadge } from '@/components/common/StatusBadge';
import { Button } from '@/components/common/Button';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import {
  ShieldCheck,
  Server,
  Layers,
  ArrowRight,
  Terminal,
  Clock,
  Sparkles,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  const { data: health, isLoading, isError, refetch } = useQuery({
    queryKey: ['system-health'],
    queryFn: healthApi.getHealth,
  });

  const phases = [
    { num: '01', name: 'Company Acquisition', steps: 'Steps 1–4', status: 'Planned' },
    { num: '02', name: 'Job Requirement Mgmt', steps: 'Steps 5–9', status: 'Planned' },
    { num: '03', name: 'Student Registration', steps: 'Steps 10–14', status: 'Planned' },
    { num: '04', name: 'Student Preparation', steps: 'Steps 15–23', status: 'Planned' },
    { num: '05', name: 'Company Submission', steps: 'Steps 24–28', status: 'Planned' },
    { num: '06', name: 'Interview Management', steps: 'Steps 29–33', status: 'Planned' },
    { num: '07', name: 'Interview Tracking', steps: 'Steps 34–35', status: 'Planned' },
    { num: '08', name: 'Placement Management', steps: 'Steps 36–41', status: 'Planned' },
    { num: '09', name: 'Feedback Collection', steps: '360° Rubrics', status: 'Planned' },
    { num: '10', name: 'CRM Database Update', steps: 'Entity Sync', status: 'Planned' },
    { num: '11', name: 'Reports & Analytics', steps: 'Funnels & CTC', status: 'Planned' },
    { num: '12', name: 'Automated Follow-Up', steps: 'Daemon Worker', status: 'Planned' },
    { num: '13', name: 'Continuous Improvement', steps: 'Curriculum Gaps', status: 'Planned' },
  ];

  return (
    <div className="space-y-8">
      {/* Hero Welcome Banner */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-gqt-navy via-gqt-navy-light to-gqt-blue text-white p-8 sm:p-10 shadow-lg border border-gqt-navy/40">
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur text-xs font-semibold tracking-wide uppercase border border-white/20">
            <Sparkles className="w-3.5 h-3.5 text-gqt-blue-accent" />
            Greenfield Foundation Verified
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight leading-tight">
            GQT HRMS &amp; Recruitment CRM
          </h1>
          <p className="text-sm sm:text-base text-blue-100 max-w-2xl leading-relaxed">
            Production-oriented corporate recruitment and institutional placement platform engineered from scratch for Global Quest Technologies. Built around the authoritative 13 workflow phases and 41 operational steps.
          </p>
          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link to="/diagnostics">
              <Button variant="secondary" size="md" className="bg-white text-gqt-navy hover:bg-blue-50 font-bold">
                Run Diagnostics Probe
                <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
            <a
              href="http://localhost:8000/api/v1/schema/swagger/"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Button variant="outline" size="md" className="border-white/30 text-white hover:bg-white/10 bg-transparent">
                OpenAPI Specification
              </Button>
            </a>
          </div>
        </div>
      </section>

      {/* Grid: Foundation Invariants & Live System Probe */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Foundation Metric Cards */}
        <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Card>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-gqt-blue-light flex items-center justify-center text-gqt-blue">
                  <Server className="w-5 h-5" />
                </div>
                <StatusBadge variant="success" label="Active" />
              </div>
              <div>
                <h4 className="text-base font-bold text-gqt-charcoal">Backend Engine</h4>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Django 5.1.15 + Django REST Framework with strict 5-Layer pattern and versioned REST endpoints (/api/v1/).
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <StatusBadge variant="success" label="Enforced" />
              </div>
              <div>
                <h4 className="text-base font-bold text-gqt-charcoal">Security Baseline</h4>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Fail-closed production settings, sensitive data redaction filter, correlation tracing, and zero secret leakage.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-purple-50 flex items-center justify-center text-purple-600">
                  <Layers className="w-5 h-5" />
                </div>
                <StatusBadge variant="info" label="Ready" />
              </div>
              <div>
                <h4 className="text-base font-bold text-gqt-charcoal">Supabase PostgreSQL 16</h4>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Psycopg 3.2+ driver with SSL require support, connection pooler optimization, and migration consistency checks.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center text-amber-600">
                  <Terminal className="w-5 h-5" />
                </div>
                <StatusBadge variant="warning" label="Phase 1 Ready" />
              </div>
              <div>
                <h4 className="text-base font-bold text-gqt-charcoal">Automated QA Suites</h4>
                <p className="text-xs text-gqt-neutral-500 mt-1">
                  Backend Pytest automated test suite and frontend Vitest component tests with TypeScript strict compiler checks.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Live Health Check Widget */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>System Liveness</CardTitle>
              <StatusBadge
                variant={health?.status === 'UP' ? 'success' : 'danger'}
                label={health?.status || 'Probing...'}
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col justify-between space-y-4">
            {isLoading && <LoadingState message="Connecting to API..." />}
            {isError && (
              <ErrorState
                title="API Unavailable"
                message="Ensure Django backend is running at http://localhost:8000"
                onRetry={() => refetch()}
              />
            )}
            {health && (
              <div className="space-y-3 text-xs">
                <div className="p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200/80 space-y-2">
                  <div className="flex justify-between py-1 border-b border-gqt-neutral-200/60">
                    <span className="text-gqt-neutral-500">Service:</span>
                    <span className="font-semibold text-gqt-navy">{health.service}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-gqt-neutral-200/60">
                    <span className="text-gqt-neutral-500">Version:</span>
                    <span className="font-semibold text-gqt-charcoal">{health.version}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-gqt-neutral-200/60">
                    <span className="text-gqt-neutral-500">Environment:</span>
                    <span className="font-semibold text-gqt-blue capitalize">{health.environment}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-gqt-neutral-500">Correlation ID:</span>
                    <span className="font-mono text-[10px] text-gqt-charcoal truncate max-w-[140px]">
                      {health.correlation_id}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-gqt-neutral-400 text-[11px]">
                  <Clock className="w-3.5 h-3.5" />
                  Checked: {new Date(health.timestamp).toLocaleTimeString()}
                </div>
              </div>
            )}
            <Link to="/diagnostics" className="pt-2">
              <Button variant="outline" size="sm" className="w-full">
                View Full Diagnostics
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* 13 Phases Architecture Roadmap */}
      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <CardTitle>13-Phase Workflow Lifecycle</CardTitle>
              <p className="text-xs text-gqt-neutral-500 mt-1">
                Authoritative institutional recruitment workflow from GQT HRMS specifications (41 Steps).
              </p>
            </div>
            <StatusBadge variant="info" label="Foundation Stage" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3.5">
            {phases.map((p) => (
              <div
                key={p.num}
                className="p-3.5 rounded-xl border border-gqt-neutral-200 bg-white hover:border-gqt-blue/40 transition-colors space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-black text-gqt-blue">Phase {p.num}</span>
                  <StatusBadge variant="neutral" label={p.steps} showDot={false} className="text-[10px] px-2 py-0" />
                </div>
                <h5 className="text-xs font-bold text-gqt-charcoal truncate">{p.name}</h5>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
