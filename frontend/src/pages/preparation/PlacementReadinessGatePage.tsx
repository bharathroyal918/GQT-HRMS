import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Award,
  CheckCircle2,
  Lock,
  Search,
  ShieldCheck,
  UserCheck,
  XCircle,
} from 'lucide-react';
import { preparationApi } from '@/api/preparationApi';
import { studentsApi } from '@/api/studentsApi';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { StudentReadinessSnapshot } from '@/types/preparation';

export const PlacementReadinessGatePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const userRoles = user?.roles || [];
  const canCertify =
    user?.is_superuser || userRoles.some(r => r === 'PLACEMENT_HEAD' || r === 'ADMIN');

  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  const [certModalOpen, setCertModalOpen] = useState(false);
  const [isApprovedDecision, setIsApprovedDecision] = useState(true);
  const [certNotes, setCertNotes] = useState('');
  const [certError, setCertError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch student profiles
  const {
    data: profiles = [],
    isLoading: profilesLoading,
    error: profilesError,
  } = useQuery({
    queryKey: ['students-profiles-for-gate'],
    queryFn: () => studentsApi.listProfiles(),
  });

  // Fetch certifications
  const {
    data: certifications = [],
    isLoading: certsLoading,
  } = useQuery({
    queryKey: ['preparation-certifications'],
    queryFn: () => preparationApi.listPlacementCertifications(),
  });

  // Fetch readiness snapshot for selected student
  const {
    data: snapshot,
    isLoading: snapshotLoading,
  } = useQuery<StudentReadinessSnapshot>({
    queryKey: ['preparation-readiness-snapshot', selectedStudentId],
    queryFn: () => preparationApi.getStudentReadinessSnapshot(selectedStudentId!),
    enabled: !!selectedStudentId,
  });

  // Certify readiness mutation
  const certMutation = useMutation({
    mutationFn: () =>
      preparationApi.certifyPlacementReadiness({
        student_id: selectedStudentId!,
        approved_resume_id: snapshot?.current_resume_id || '',
        is_approved: isApprovedDecision,
        notes: certNotes,
      }),
    onSuccess: () => {
      setCertModalOpen(false);
      setCertError(null);
      setCertNotes('');
      queryClient.invalidateQueries({ queryKey: ['preparation-certifications'] });
      queryClient.invalidateQueries({ queryKey: ['preparation-readiness-snapshot', selectedStudentId] });
    },
    onError: (err: any) => {
      setCertError(err.response?.data?.detail || err.message || 'Failed to certify readiness.');
    },
  });

  if (profilesLoading || certsLoading) {
    return <LoadingState message="Loading placement readiness dashboard & candidate criteria..." />;
  }

  if (profilesError) {
    return <ErrorState message="Could not load candidate roster." />;
  }

  const certifiedCount = certifications.filter(c => c.is_approved_for_placements).length;
  const filteredProfiles = profiles.filter(
    p =>
      p.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Final Placement Resume Approval Gate
          </h1>
          <p className="text-sm text-slate-500">
            Workflow Step 23: Placement Head Formal Readiness Certification Gate (Unlocks Phase 7 Drive Submissions)
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs px-3 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-full font-semibold flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" />
            Mandatory Gate for Phase 7
          </span>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Registered Candidates</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">{profiles.length}</h3>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <UserCheck className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Certified for Placements</p>
                <h3 className="text-2xl font-bold text-emerald-600 mt-1">{certifiedCount}</h3>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <ShieldCheck className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Readiness Rate</p>
                <h3 className="text-2xl font-bold text-indigo-600 mt-1">
                  {profiles.length > 0 ? `${Math.round((certifiedCount / profiles.length) * 100)}%` : '0%'}
                </h3>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <Award className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Candidates Queue (2 cols) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Candidate Readiness Roster</CardTitle>
                  <CardDescription>Select any candidate to inspect all 6 preparation milestones</CardDescription>
                </div>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    placeholder="Search candidate..."
                    className="pl-9 pr-3 py-1.5 text-sm rounded-md border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredProfiles.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-sm">No candidates matching search.</div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Candidate</th>
                        <th className="py-3 px-4">Department</th>
                        <th className="py-3 px-4">CGPA</th>
                        <th className="py-3 px-4">Placement Certified</th>
                        <th className="py-3 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredProfiles.map(p => {
                        const isCert = certifications.some(
                          c => c.student === p.id && c.is_approved_for_placements
                        );
                        return (
                          <tr
                            key={p.id}
                            className={`hover:bg-slate-50/50 cursor-pointer ${
                              selectedStudentId === p.id ? 'bg-blue-50/40' : ''
                            }`}
                            onClick={() => setSelectedStudentId(p.id)}
                          >
                            <td className="py-3 px-4">
                              <div className="font-medium text-slate-900">{p.full_name}</div>
                              <div className="text-xs text-slate-400">{p.roll_number}</div>
                            </td>
                            <td className="py-3 px-4 text-xs">{p.department}</td>
                            <td className="py-3 px-4 font-mono font-semibold text-slate-800">{p.cgpa}</td>
                            <td className="py-3 px-4">
                              <StatusBadge
                                variant={isCert ? 'success' : 'neutral'}
                                label={isCert ? 'Certified' : 'Pending'}
                              />
                            </td>
                            <td className="py-3 px-4 text-right">
                              <button
                                onClick={e => {
                                  e.stopPropagation();
                                  setSelectedStudentId(p.id);
                                }}
                                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                              >
                                View Criteria
                              </button>
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
        </div>

        {/* Selected Candidate Gate Decision Drawer (1 col) */}
        <div>
          {selectedStudentId ? (
            snapshotLoading ? (
              <LoadingState message="Loading criteria snapshot..." />
            ) : snapshot ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>Preparation Gate Status</CardTitle>
                    <StatusBadge
                      variant={snapshot.is_placement_certified ? 'success' : 'neutral'}
                      label={snapshot.is_placement_certified ? 'Certified' : 'Pending Gate'}
                    />
                  </div>
                  <CardDescription>
                    {snapshot.student_name} ({snapshot.roll_number}) • Resume{' '}
                    {snapshot.current_resume_version ? `v${snapshot.current_resume_version}` : 'None'}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Criteria Checklist Pills */}
                  <div className="space-y-2 text-xs">
                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.resume_review_approved
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.resume_review_approved ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">1. Resume Review (Step 15)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.resume_review_approved ? 'Trainer Approved' : 'Incomplete / Pending'}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.aptitude_assessment_passed
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.aptitude_assessment_passed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">2. Aptitude Test (Step 17)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.aptitude_assessment_passed
                          ? `Passed (${snapshot.criteria.aptitude_score} Marks)`
                          : 'Not Passed'}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.technical_assessment_passed
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.technical_assessment_passed ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">3. Technical Test (Step 18)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.technical_assessment_passed
                          ? `Passed (${snapshot.criteria.technical_score} Marks)`
                          : 'Not Passed'}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.communication_attended
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.communication_attended ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">4. Comm Workshop (Step 19)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.communication_attended ? 'Attended' : 'Absent'}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.grooming_certified
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.grooming_certified ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">5. Corporate Grooming (Step 20)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.grooming_certified ? 'Certified' : 'Uncertified'}
                      </span>
                    </div>

                    <div
                      className={`flex items-center justify-between p-2.5 rounded-lg border ${
                        snapshot.criteria.mock_interview_ready
                          ? 'bg-emerald-50/60 border-emerald-200 text-emerald-800'
                          : 'bg-rose-50/60 border-rose-200 text-rose-800'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {snapshot.criteria.mock_interview_ready ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                        ) : (
                          <XCircle className="w-4 h-4 text-rose-500" />
                        )}
                        <span className="font-semibold">6. Mock Interview (Step 22)</span>
                      </div>
                      <span className="font-medium">
                        {snapshot.criteria.mock_interview_ready
                          ? `Ready (${snapshot.criteria.mock_total_score}/40)`
                          : 'Needs Practice'}
                      </span>
                    </div>
                  </div>

                  {/* Certification Action */}
                  <div className="pt-3 border-t border-slate-100">
                    {canCertify ? (
                      <Button
                        id="certify-readiness-btn"
                        onClick={() => setCertModalOpen(true)}
                        className={`w-full text-white text-xs ${
                          snapshot.all_criteria_met
                            ? 'bg-emerald-600 hover:bg-emerald-700'
                            : 'bg-slate-900 hover:bg-slate-800'
                        }`}
                      >
                        <ShieldCheck className="w-4 h-4 mr-1.5" />
                        Placement Head Certification Decision
                      </Button>
                    ) : (
                      <div className="p-3 bg-slate-50 text-slate-500 text-xs rounded-lg text-center flex items-center justify-center gap-1.5">
                        <Lock className="w-3.5 h-3.5 text-slate-400" />
                        Formal certification restricted to Placement Head / Admin.
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ) : null
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-slate-500 text-sm">
                Select a candidate from the roster to verify preparation criteria and authorize readiness.
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Placement Head Formal Gate Certification Modal */}
      {certModalOpen && snapshot && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">
              Placement Readiness Certification Gate (Step 23)
            </h3>
            <p className="text-xs text-slate-500">
              Candidate: <span className="font-semibold text-slate-900">{snapshot.student_name}</span> (
              {snapshot.roll_number}) • Locked Resume:{' '}
              <span className="font-mono font-semibold">
                v{snapshot.current_resume_version || 1}
              </span>
            </p>

            {certError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {certError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Certification Decision</label>
                <select
                  value={isApprovedDecision ? 'TRUE' : 'FALSE'}
                  onChange={e => setIsApprovedDecision(e.target.value === 'TRUE')}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="TRUE">CERTIFY READY FOR PLACEMENT DRIVES (is_approved_for_placements = True)</option>
                  <option value="FALSE">RETURN FOR FURTHER PREPARATION (is_approved_for_placements = False)</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Placement Head Authorization Directive</label>
                <textarea
                  rows={3}
                  value={certNotes}
                  onChange={e => setCertNotes(e.target.value)}
                  placeholder="Record formal drive clearance notes or remedial instructions..."
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setCertModalOpen(false)}>
                Cancel
              </Button>
              <Button
                id="confirm-certification-btn"
                onClick={() => certMutation.mutate()}
                disabled={certMutation.isPending || !snapshot.current_resume_id}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {certMutation.isPending ? 'Certifying...' : 'Authorize Clearance'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
