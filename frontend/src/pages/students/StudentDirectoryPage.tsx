import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText, UserCheck, X, Award, GraduationCap, Send, Star } from 'lucide-react';
import { studentsApi } from '@/api/studentsApi';
import { crmApi } from '@/api/crmApi';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Input } from '@/components/common/Input';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';

export const StudentDirectoryPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [selectedYear, setSelectedYear] = useState('');
  const [selectedStudentIdFor360, setSelectedStudentIdFor360] = useState<string | null>(null);

  const {
    data: profiles,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['student-profiles', searchTerm, selectedDept, selectedYear],
    queryFn: () =>
      studentsApi.listProfiles({
        search: searchTerm || undefined,
        department: selectedDept || undefined,
        graduation_year: selectedYear || undefined,
      }),
  });

  const { data: student360Data, isLoading: is360Loading } = useQuery({
    queryKey: ['student-360', selectedStudentIdFor360],
    queryFn: () => (selectedStudentIdFor360 ? crmApi.getStudent360(selectedStudentIdFor360) : null),
    enabled: Boolean(selectedStudentIdFor360),
  });

  const { data: studentTimelineData } = useQuery({
    queryKey: ['student-timeline', selectedStudentIdFor360],
    queryFn: () => (selectedStudentIdFor360 ? crmApi.getStudentTimeline(selectedStudentIdFor360) : null),
    enabled: Boolean(selectedStudentIdFor360),
  });

  if (isLoading) return <LoadingState message="Loading registered students..." />;
  if (error) return <ErrorState message="Could not load student directory." />;

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-semibold tracking-wider uppercase text-gqt-blue bg-blue-50 px-2 py-0.5 rounded">
            Step 11 & 12 Directory
          </span>
          <h1 className="text-2xl font-bold text-gqt-navy mt-1">Student Talent Directory</h1>
          <p className="text-sm text-gqt-neutral-500">
            Enrolled student profiles and uploaded placement resume documents.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <Card>
        <CardContent className="pt-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Input
              placeholder="Search by name, roll no, email..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
            />
            <select
              value={selectedDept}
              onChange={e => setSelectedDept(e.target.value)}
              className="rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">All Departments</option>
              <option value="Computer Science">Computer Science & Engineering</option>
              <option value="Information Science">Information Science & Engineering</option>
              <option value="Electronics">Electronics & Communication</option>
              <option value="Mechanical">Mechanical Engineering</option>
            </select>
            <select
              value={selectedYear}
              onChange={e => setSelectedYear(e.target.value)}
              className="rounded-md border border-gqt-neutral-300 px-3 py-2 text-sm"
            >
              <option value="">All Passing Batches</option>
              <option value="2024">2024</option>
              <option value="2025">2025</option>
              <option value="2026">2026</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Profiles Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Registered Students ({profiles?.length || 0})</CardTitle>
          <CardDescription>
            All registered candidates available for eligibility verification and campus hiring drives.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!profiles || profiles.length === 0 ? (
            <p className="text-sm text-gqt-neutral-500 py-8 text-center">
              No students found matching your search criteria.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-gqt-neutral-200 text-xs font-semibold text-gqt-neutral-500 uppercase tracking-wider">
                    <th className="pb-3">Roll Number</th>
                    <th className="pb-3">Candidate</th>
                    <th className="pb-3">Discipline</th>
                    <th className="pb-3">CGPA</th>
                    <th className="pb-3">Batch</th>
                    <th className="pb-3">Active Resume</th>
                    <th className="pb-3">Placement Verification</th>
                    <th className="pb-3 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gqt-neutral-100">
                  {profiles.map(p => (
                    <tr key={p.id} className="hover:bg-gqt-neutral-50/50">
                      <td className="py-3 font-mono font-bold text-xs text-gqt-navy">{p.roll_number}</td>
                      <td className="py-3">
                        <span className="font-semibold text-gqt-navy block">{p.full_name}</span>
                        <span className="text-xs text-gqt-neutral-400">{p.institutional_email}</span>
                      </td>
                      <td className="py-3 text-gqt-neutral-600">{p.department}</td>
                      <td className="py-3 font-semibold text-gqt-navy">{p.cgpa}</td>
                      <td className="py-3 text-gqt-neutral-500">{p.graduation_year}</td>
                      <td className="py-3">
                        {p.current_resume ? (
                          <a
                            href={studentsApi.getResumeDownloadUrl(p.current_resume.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-xs font-medium text-gqt-blue hover:underline"
                          >
                            <FileText className="w-3.5 h-3.5 mr-1" />
                            v{p.current_resume.version_number} (Active)
                          </a>
                        ) : (
                          <span className="text-xs text-amber-600 font-medium">Pending Upload</span>
                        )}
                      </td>
                      <td className="py-3">
                        {p.is_verified_by_placement ? (
                          <StatusBadge variant="success" label="Verified" />
                        ) : (
                          <StatusBadge variant="neutral" label="Unverified" />
                        )}
                      </td>
                      <td className="py-3 text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                          onClick={() => setSelectedStudentIdFor360(p.id)}
                        >
                          360° Profile
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* 360-Degree Candidate Profile Modal */}
      {selectedStudentIdFor360 && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-3xl w-full max-h-[90vh] flex flex-col overflow-hidden border border-gqt-neutral-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-gqt-neutral-100 flex items-center justify-between bg-gqt-neutral-50/70">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-50 text-gqt-blue">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-gqt-navy">
                    {student360Data?.data?.student?.full_name || 'Candidate Profile'}
                  </h3>
                  <p className="text-xs text-gqt-neutral-500 font-mono">
                    {student360Data?.data?.student?.roll_number} • {student360Data?.data?.student?.department}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedStudentIdFor360(null)}
                className="p-1 rounded hover:bg-gqt-neutral-200 text-gqt-neutral-500 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-6 text-xs text-gqt-charcoal">
              {is360Loading ? (
                <div className="py-12">
                  <LoadingState message="Assembling unified 360° candidate history..." />
                </div>
              ) : !student360Data?.data ? (
                <div className="text-center py-8 text-gqt-neutral-500">
                  Could not load candidate profile details.
                </div>
              ) : (
                <>
                  {/* High-Level Candidate Status Badges */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-[10px] uppercase font-bold text-gqt-neutral-500">Academic CGPA</span>
                      <p className="text-base font-extrabold text-gqt-navy mt-0.5">
                        {student360Data.data.student.cgpa ?? 'N/A'}
                      </p>
                    </div>
                    <div className="p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-[10px] uppercase font-bold text-gqt-neutral-500">Readiness Gate</span>
                      <div className="mt-0.5">
                        <StatusBadge
                          variant={student360Data.data.readiness_gate.is_certified ? 'success' : 'warning'}
                          label={student360Data.data.readiness_gate.is_certified ? 'Certified' : 'Not Certified'}
                        />
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-[10px] uppercase font-bold text-gqt-neutral-500">Placement Outcome</span>
                      <div className="mt-0.5">
                        <StatusBadge
                          variant={
                            student360Data.data.overall_placement_outcome === 'JOINED'
                              ? 'success'
                              : student360Data.data.overall_placement_outcome === 'SELECTED'
                              ? 'info'
                              : 'neutral'
                          }
                          label={student360Data.data.overall_placement_outcome}
                        />
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-gqt-neutral-50 border border-gqt-neutral-200">
                      <span className="text-[10px] uppercase font-bold text-gqt-neutral-500">Backlogs</span>
                      <p className="text-base font-extrabold text-gqt-navy mt-0.5">
                        {student360Data.data.student.active_backlogs}
                      </p>
                    </div>
                  </div>

                  {/* Resumes List */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-2 flex items-center gap-1.5">
                      <FileText className="w-4 h-4 text-gqt-blue" />
                      Resume Version History ({student360Data.data.resumes.length})
                    </h4>
                    <div className="border border-gqt-neutral-200 rounded-lg divide-y divide-gqt-neutral-100 overflow-hidden">
                      {student360Data.data.resumes.map((r) => (
                        <div key={r.id} className="p-3 flex items-center justify-between hover:bg-gqt-neutral-50/50">
                          <div>
                            <span className="font-semibold text-gqt-navy">
                              Version {r.version_number}: {r.file_name}
                            </span>
                            <p className="text-[11px] text-gqt-neutral-500">
                              Uploaded on {new Date(r.created_at).toLocaleDateString()} • {(r.file_size_bytes / 1024).toFixed(1)} KB
                            </p>
                          </div>
                          {r.is_current && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                              Active Current
                            </span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Placement History */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-2 flex items-center gap-1.5">
                      <Award className="w-4 h-4 text-emerald-600" />
                      Placement & Offer Letter Outcomes ({student360Data.data.placement_history.length})
                    </h4>
                    {student360Data.data.placement_history.length === 0 ? (
                      <p className="text-gqt-neutral-400 italic">No placement selections recorded yet.</p>
                    ) : (
                      <div className="border border-gqt-neutral-200 rounded-lg divide-y divide-gqt-neutral-100 overflow-hidden">
                        {student360Data.data.placement_history.map((ps) => (
                          <div key={ps.id} className="p-3 flex items-center justify-between hover:bg-gqt-neutral-50/50">
                            <div>
                              <span className="font-semibold text-gqt-navy">{ps.company_name}</span>
                              <p className="text-[11px] text-gqt-neutral-500">
                                {ps.job_title} • {ps.designation_offered} • {ps.offered_ctc ? `₹${ps.offered_ctc.toLocaleString()}` : 'N/A'}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              <StatusBadge variant="info" label={ps.status} />
                              <StatusBadge
                                variant={ps.joining_status === 'JOINED' ? 'success' : 'neutral'}
                                label={ps.joining_status}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Trainer Evaluations */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-2 flex items-center gap-1.5">
                      <Star className="w-4 h-4 text-amber-500" />
                      Trainer Readiness Evaluations ({student360Data.data.trainer_evaluations.length})
                    </h4>
                    {student360Data.data.trainer_evaluations.length === 0 ? (
                      <p className="text-gqt-neutral-400 italic">No trainer evaluations submitted yet.</p>
                    ) : (
                      <div className="space-y-2">
                        {student360Data.data.trainer_evaluations.map((te) => (
                          <div key={te.id} className="p-3 rounded-lg border border-gqt-neutral-200 bg-gqt-neutral-50/50">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-gqt-navy">Evaluated by {te.trainer_name}</span>
                              <StatusBadge variant="info" label={te.student_readiness_display} />
                            </div>
                            <p className="text-[11px] text-gqt-neutral-600 mt-1">
                              <strong>Areas for Improvement:</strong> {te.areas_for_improvement}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Communication History */}
                  <div>
                    <h4 className="text-xs font-bold uppercase tracking-wider text-gqt-navy mb-2 flex items-center gap-1.5">
                      <Send className="w-4 h-4 text-gqt-blue" />
                      Candidate Communication Timeline ({studentTimelineData?.data?.length || 0})
                    </h4>
                    {!studentTimelineData?.data || studentTimelineData.data.length === 0 ? (
                      <p className="text-gqt-neutral-400 italic">No communication notifications logged for this candidate.</p>
                    ) : (
                      <div className="border border-gqt-neutral-200 rounded-lg divide-y divide-gqt-neutral-100 overflow-hidden">
                        {studentTimelineData.data.map((evt) => (
                          <div key={evt.id} className="p-3 hover:bg-gqt-neutral-50/50">
                            <div className="flex items-center justify-between">
                              <span className="font-semibold text-gqt-navy">{evt.subject}</span>
                              <span className="text-[10px] font-mono text-gqt-neutral-400">
                                {new Date(evt.timestamp).toLocaleString()}
                              </span>
                            </div>
                            <p className="text-[11px] text-gqt-neutral-600 mt-0.5">{evt.summary}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-gqt-neutral-50 border-t border-gqt-neutral-100 flex justify-end">
              <Button size="sm" variant="outline" onClick={() => setSelectedStudentIdFor360(null)}>
                Close Profile
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
