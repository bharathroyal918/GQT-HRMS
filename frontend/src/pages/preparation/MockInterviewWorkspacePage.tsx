import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Calendar,
  CheckCircle2,
  ExternalLink,
  Search,
  Star,
  Users,
  Video,
} from 'lucide-react';
import { preparationApi } from '@/api/preparationApi';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { MockInterview, MockReadinessRecommendation } from '@/types/preparation';

export const MockInterviewWorkspacePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const userRoles = user?.roles || [];
  const isEvaluatorOrStaff =
    user?.is_superuser ||
    userRoles.some(r => ['EVALUATOR', 'TRAINER', 'PLACEMENT_OFFICER', 'PLACEMENT_HEAD', 'ADMIN'].includes(r));
  const isStaff =
    user?.is_superuser ||
    userRoles.some(r => ['PLACEMENT_OFFICER', 'PLACEMENT_HEAD', 'ADMIN'].includes(r));

  const [selectedMock, setSelectedMock] = useState<MockInterview | null>(null);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [evaluateModalOpen, setEvaluateModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Schedule Form State
  const [studentId, setStudentId] = useState('');
  const [evaluatorId, setEvaluatorId] = useState(user?.id || '');
  const [scheduledAt, setScheduledAt] = useState('');
  const [interviewType, setInterviewType] = useState<'TECHNICAL' | 'HR' | 'COMBINED'>('COMBINED');
  const [meetingLink, setMeetingLink] = useState('');
  const [scheduleNotes, setScheduleNotes] = useState('');
  const [scheduleError, setScheduleError] = useState<string | null>(null);

  // Rubric Evaluation Form State
  const [targetMockId, setTargetMockId] = useState('');
  const [technicalScore, setTechnicalScore] = useState(8);
  const [problemSolvingScore, setProblemSolvingScore] = useState(8);
  const [communicationScore, setCommunicationScore] = useState(8);
  const [professionalScore, setProfessionalScore] = useState(8);
  const [technicalFeedback, setTechnicalFeedback] = useState('');
  const [communicationFeedback, setCommunicationFeedback] = useState('');
  const [improvementSuggestions, setImprovementSuggestions] = useState('');
  const [readinessRec, setReadinessRec] = useState<MockReadinessRecommendation>('READY_FOR_PLACEMENTS');
  const [evalError, setEvalError] = useState<string | null>(null);

  // Fetch mock interviews
  const {
    data: mocks = [],
    isLoading: mocksLoading,
    error: mocksError,
  } = useQuery({
    queryKey: ['preparation-mock-interviews'],
    queryFn: () => preparationApi.listMockInterviews(),
  });

  // Schedule mutation
  const scheduleMutation = useMutation({
    mutationFn: () =>
      preparationApi.scheduleMockInterview({
        student_id: studentId,
        evaluator_id: evaluatorId,
        scheduled_at: scheduledAt,
        interview_type: interviewType,
        meeting_link: meetingLink,
        notes: scheduleNotes,
      }),
    onSuccess: () => {
      setScheduleModalOpen(false);
      setScheduleError(null);
      setStudentId('');
      setMeetingLink('');
      setScheduleNotes('');
      queryClient.invalidateQueries({ queryKey: ['preparation-mock-interviews'] });
    },
    onError: (err: any) => {
      setScheduleError(err.response?.data?.detail || err.message || 'Failed to schedule mock interview.');
    },
  });

  // Evaluation mutation
  const evalMutation = useMutation({
    mutationFn: () =>
      preparationApi.submitMockEvaluation({
        mock_interview_id: targetMockId,
        technical_competence_score: technicalScore,
        problem_solving_score: problemSolvingScore,
        communication_clarity_score: communicationScore,
        professional_readiness_score: professionalScore,
        technical_feedback: technicalFeedback,
        communication_feedback: communicationFeedback,
        improvement_suggestions: improvementSuggestions,
        readiness_recommendation: readinessRec,
      }),
    onSuccess: () => {
      setEvaluateModalOpen(false);
      setEvalError(null);
      queryClient.invalidateQueries({ queryKey: ['preparation-mock-interviews'] });
    },
    onError: (err: any) => {
      setEvalError(err.response?.data?.detail || err.message || 'Failed to submit evaluation scorecard.');
    },
  });

  if (mocksLoading) {
    return <LoadingState message="Loading mock interviews and scorecards..." />;
  }

  if (mocksError) {
    return <ErrorState message="Could not load mock interviews." />;
  }

  const completedCount = mocks.filter(m => m.status === 'COMPLETED').length;
  const readyCount = mocks.filter(
    m => m.evaluation?.readiness_recommendation === 'READY_FOR_PLACEMENTS'
  ).length;

  const filteredMocks = mocks.filter(
    m =>
      m.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.student_roll_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.evaluator_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            One-on-One Mock Interviews & Rubrics
          </h1>
          <p className="text-sm text-slate-500">
            Workflow Steps 21–22: Simulated Technical & HR Interviews with Comprehensive Scorecards
          </p>
        </div>
        <div className="flex gap-2">
          {isStaff && (
            <Button
              id="schedule-mock-interview-btn"
              onClick={() => setScheduleModalOpen(true)}
              className="bg-slate-900 hover:bg-slate-800 text-white flex items-center gap-2"
            >
              <Calendar className="w-4 h-4" />
              Schedule Mock Interview
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Scheduled / Total Mocks</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">{mocks.length}</h3>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <Users className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Evaluations Completed</p>
                <h3 className="text-2xl font-bold text-indigo-600 mt-1">{completedCount}</h3>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <CheckCircle2 className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Certified Ready for Placements</p>
                <h3 className="text-2xl font-bold text-emerald-600 mt-1">{readyCount}</h3>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <Star className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Table (2 cols) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Mock Interview Sessions</CardTitle>
                  <CardDescription>Scheduled rounds with assigned evaluators and current status</CardDescription>
                </div>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    placeholder="Search candidate or evaluator..."
                    className="pl-9 pr-3 py-1.5 text-sm rounded-md border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-blue-600"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {filteredMocks.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <Video className="w-12 h-12 mx-auto text-slate-300 mb-2" />
                  <p>No mock interview sessions scheduled.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Candidate</th>
                        <th className="py-3 px-4">Interview Type</th>
                        <th className="py-3 px-4">Evaluator</th>
                        <th className="py-3 px-4">Scheduled Date</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredMocks.map(m => (
                        <tr key={m.id} className="hover:bg-slate-50/50">
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-900">{m.student_name}</div>
                            <div className="text-xs text-slate-400">{m.student_roll_number}</div>
                          </td>
                          <td className="py-3 px-4 text-xs font-semibold text-slate-700">{m.interview_type}</td>
                          <td className="py-3 px-4 text-xs text-slate-600">{m.evaluator_name}</td>
                          <td className="py-3 px-4 text-xs text-slate-500">
                            {new Date(m.scheduled_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                          </td>
                          <td className="py-3 px-4">
                            <StatusBadge
                              variant={m.status === 'COMPLETED' ? 'success' : m.status === 'CANCELLED' ? 'danger' : 'info'}
                              label={m.status}
                            />
                          </td>
                          <td className="py-3 px-4 text-right space-x-2">
                            <button
                              onClick={() => setSelectedMock(m)}
                              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              Details
                            </button>
                            {isEvaluatorOrStaff && m.status !== 'COMPLETED' && (
                              <Button
                                id={`evaluate-mock-${m.id}`}
                                size="sm"
                                onClick={() => {
                                  setTargetMockId(m.id);
                                  setEvaluateModalOpen(true);
                                }}
                                className="text-xs bg-slate-900 text-white"
                              >
                                Evaluate
                              </Button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Selected Interview & Scorecard Inspector (1 col) */}
        <div>
          {selectedMock ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Session & Scorecard</CardTitle>
                  <StatusBadge
                    variant={selectedMock.status === 'COMPLETED' ? 'success' : 'info'}
                    label={selectedMock.status}
                  />
                </div>
                <CardDescription>
                  {selectedMock.student_name} ({selectedMock.student_roll_number}) • Evaluator: {selectedMock.evaluator_name}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedMock.meeting_link && (
                  <div className="p-3 bg-blue-50/70 border border-blue-200/60 rounded-lg text-xs flex items-center justify-between">
                    <span className="font-medium text-blue-900">Virtual Meeting Venue</span>
                    <a
                      href={selectedMock.meeting_link}
                      target="_blank"
                      rel="noreferrer"
                      className="text-blue-600 hover:underline flex items-center gap-1 font-semibold"
                    >
                      Join Link <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                )}

                {selectedMock.evaluation ? (
                  <div className="space-y-3 pt-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase text-slate-500">Readiness Decision</span>
                      <StatusBadge
                        variant={selectedMock.evaluation.readiness_recommendation === 'READY_FOR_PLACEMENTS' ? 'success' : 'warning'}
                        label={selectedMock.evaluation.readiness_recommendation === 'READY_FOR_PLACEMENTS' ? 'Ready' : selectedMock.evaluation.readiness_recommendation === 'NEEDS_PRACTICE' ? 'Needs Practice' : 'Not Ready'}
                      />
                    </div>

                    <div className="p-4 bg-slate-900 text-white rounded-lg text-center">
                      <div className="text-3xl font-extrabold">{selectedMock.evaluation.total_score} / 40</div>
                      <div className="text-xs text-slate-300 mt-1">Overall Rubric Scorecard</div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2 bg-slate-50 rounded">
                        <span className="text-slate-500">Technical Depth:</span>
                        <span className="float-right font-bold">{selectedMock.evaluation.technical_competence_score}/10</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <span className="text-slate-500">Problem Solving:</span>
                        <span className="float-right font-bold">{selectedMock.evaluation.problem_solving_score}/10</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <span className="text-slate-500">Communication:</span>
                        <span className="float-right font-bold">{selectedMock.evaluation.communication_clarity_score}/10</span>
                      </div>
                      <div className="p-2 bg-slate-50 rounded">
                        <span className="text-slate-500">Professionalism:</span>
                        <span className="float-right font-bold">{selectedMock.evaluation.professional_readiness_score}/10</span>
                      </div>
                    </div>

                    <div className="text-xs space-y-2">
                      <div>
                        <span className="font-semibold text-slate-700">Technical Notes:</span>
                        <p className="text-slate-600 bg-slate-50 p-2 rounded mt-0.5">{selectedMock.evaluation.technical_feedback}</p>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700">Communication Notes:</span>
                        <p className="text-slate-600 bg-slate-50 p-2 rounded mt-0.5">{selectedMock.evaluation.communication_feedback}</p>
                      </div>
                      <div>
                        <span className="font-semibold text-slate-700">Improvement Suggestions:</span>
                        <p className="text-amber-800 bg-amber-50 p-2 rounded mt-0.5 border border-amber-200/50">
                          {selectedMock.evaluation.improvement_suggestions}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400 text-xs">
                    Scorecard pending. Evaluator will submit rubric ratings upon session completion.
                  </div>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-slate-500 text-sm">
                Select an interview from the queue to view session notes and evaluation scorecard.
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Schedule Mock Interview Modal */}
      {scheduleModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Schedule One-on-One Mock (Step 21)</h3>

            {scheduleError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {scheduleError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Student Profile UUID</label>
                <input
                  type="text"
                  value={studentId}
                  onChange={e => setStudentId(e.target.value)}
                  placeholder="Candidate Profile UUID"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Evaluator User UUID</label>
                <input
                  type="text"
                  value={evaluatorId}
                  onChange={e => setEvaluatorId(e.target.value)}
                  placeholder="Evaluator User UUID"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Date & Time</label>
                <input
                  type="datetime-local"
                  value={scheduledAt}
                  onChange={e => setScheduledAt(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Interview Round</label>
                <select
                  value={interviewType}
                  onChange={e => setInterviewType(e.target.value as any)}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="COMBINED">Combined Technical & HR Mock</option>
                  <option value="TECHNICAL">Technical Deep-Dive</option>
                  <option value="HR">HR / Behavioral Round</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Meeting Venue / Video Link</label>
                <input
                  type="text"
                  value={meetingLink}
                  onChange={e => setMeetingLink(e.target.value)}
                  placeholder="e.g. https://meet.google.com/xxx or Conference Room 1"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Notes / Candidate Directives</label>
                <textarea
                  rows={2}
                  value={scheduleNotes}
                  onChange={e => setScheduleNotes(e.target.value)}
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setScheduleModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => scheduleMutation.mutate()}
                disabled={scheduleMutation.isPending || !studentId || !scheduledAt}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {scheduleMutation.isPending ? 'Scheduling...' : 'Confirm Schedule'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Evaluator Rubric Scorecard Modal */}
      {evaluateModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-bold text-slate-900">Submit Mock Interview Scorecard (Step 22)</h3>

            {evalError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded-lg">
                {evalError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Technical Competence (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={technicalScore}
                    onChange={e => setTechnicalScore(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Problem Solving (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={problemSolvingScore}
                    onChange={e => setProblemSolvingScore(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Communication Clarity (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={communicationScore}
                    onChange={e => setCommunicationScore(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block font-medium text-slate-700 mb-1">Professional Readiness (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={professionalScore}
                    onChange={e => setProfessionalScore(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border rounded-md"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Readiness Recommendation</label>
                <select
                  value={readinessRec}
                  onChange={e => setReadinessRec(e.target.value as any)}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="READY_FOR_PLACEMENTS">Ready for Placement Drives</option>
                  <option value="NEEDS_PRACTICE">Needs Additional Practice / Minor Remediation</option>
                  <option value="NOT_READY">Not Ready — Requires Comprehensive Training</option>
                </select>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Technical Assessment Feedback</label>
                <textarea
                  rows={2}
                  value={technicalFeedback}
                  onChange={e => setTechnicalFeedback(e.target.value)}
                  placeholder="Assess technical depth, problem decomposition, and syntax..."
                  className="w-full px-3 py-1.5 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Communication & Articulation Notes</label>
                <textarea
                  rows={2}
                  value={communicationFeedback}
                  onChange={e => setCommunicationFeedback(e.target.value)}
                  placeholder="Verbal fluency, listening skills, and structured answers..."
                  className="w-full px-3 py-1.5 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Actionable Improvement Suggestions</label>
                <textarea
                  rows={2}
                  value={improvementSuggestions}
                  onChange={e => setImprovementSuggestions(e.target.value)}
                  placeholder="Concrete preparation tasks before corporate drives..."
                  className="w-full px-3 py-1.5 border rounded-md"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setEvaluateModalOpen(false)}>
                Cancel
              </Button>
              <Button
                id="submit-mock-evaluation-btn"
                onClick={() => evalMutation.mutate()}
                disabled={evalMutation.isPending || !technicalFeedback || !communicationFeedback}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {evalMutation.isPending ? 'Submitting...' : 'Submit Scorecard'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
