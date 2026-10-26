import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Award,
  CheckCircle2,
  Clock,
  HelpCircle,
  Play,
  RotateCcw,
  XCircle,
} from 'lucide-react';
import { preparationApi } from '@/api/preparationApi';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { AssessmentTest, StudentAssessmentAttempt } from '@/types/preparation';

export const StudentAssessmentsPage: React.FC = () => {
  const queryClient = useQueryClient();

  const [activeTest, setActiveTest] = useState<AssessmentTest | null>(null);
  const [currentAttempt, setCurrentAttempt] = useState<StudentAssessmentAttempt | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [runnerOpen, setRunnerOpen] = useState(false);
  const [resultModalOpen, setResultModalOpen] = useState(false);
  const [lastResult, setLastResult] = useState<StudentAssessmentAttempt | null>(null);
  const [testFilter, setTestFilter] = useState<'ALL' | 'APTITUDE' | 'TECHNICAL'>('ALL');

  // Fetch tests
  const {
    data: tests = [],
    isLoading: testsLoading,
    error: testsError,
  } = useQuery({
    queryKey: ['preparation-tests'],
    queryFn: () => preparationApi.listAssessmentTests(),
  });

  // Fetch attempts
  const {
    data: attempts = [],
    isLoading: attemptsLoading,
  } = useQuery({
    queryKey: ['preparation-attempts'],
    queryFn: () => preparationApi.listAssessmentAttempts(),
  });

  // Start attempt mutation
  const startMutation = useMutation({
    mutationFn: (testId: string) => preparationApi.startAssessmentAttempt(testId),
    onSuccess: async (attempt) => {
      // Fetch full test with questions (stripped for student)
      const fullTest = await preparationApi.getAssessmentTestDetail(attempt.test);
      setActiveTest(fullTest);
      setCurrentAttempt(attempt);
      setAnswers({});
      setRunnerOpen(true);
    },
  });

  // Submit attempt mutation
  const submitMutation = useMutation({
    mutationFn: () => preparationApi.submitAssessmentAttempt(currentAttempt!.id, answers),
    onSuccess: (result) => {
      setRunnerOpen(false);
      setLastResult(result);
      setResultModalOpen(true);
      queryClient.invalidateQueries({ queryKey: ['preparation-attempts'] });
    },
  });

  if (testsLoading || attemptsLoading) {
    return <LoadingState message="Loading assessments and scores..." />;
  }

  if (testsError) {
    return <ErrorState message="Could not load assessment tests." />;
  }

  const filteredTests = tests.filter(t => (testFilter === 'ALL' ? true : t.test_type === testFilter));

  const passedAttempts = attempts.filter(a => a.passed).length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Student Assessments Engine
          </h1>
          <p className="text-sm text-slate-500">
            Workflow Steps 17–18: Timed Aptitude & Domain-Specific Technical Assessments
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={testFilter === 'ALL' ? 'primary' : 'outline'}
            onClick={() => setTestFilter('ALL')}
            className="text-xs"
          >
            All Tracks
          </Button>
          <Button
            variant={testFilter === 'APTITUDE' ? 'primary' : 'outline'}
            onClick={() => setTestFilter('APTITUDE')}
            className="text-xs"
          >
            Aptitude (Step 17)
          </Button>
          <Button
            variant={testFilter === 'TECHNICAL' ? 'primary' : 'outline'}
            onClick={() => setTestFilter('TECHNICAL')}
            className="text-xs"
          >
            Technical (Step 18)
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Active Test Modules</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">{tests.length}</h3>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <HelpCircle className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Attempts Taken</p>
                <h3 className="text-2xl font-bold text-indigo-600 mt-1">{attempts.length}</h3>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <RotateCcw className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Qualified (Passed)</p>
                <h3 className="text-2xl font-bold text-emerald-600 mt-1">{passedAttempts}</h3>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <Award className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Available Tests Grid */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-3">Available Assessment Modules</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredTests.map(test => (
            <Card key={test.id} className="flex flex-col justify-between hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                    {test.test_type}
                  </span>
                  <span className="text-xs text-slate-400 font-medium flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    {test.duration_minutes} mins
                  </span>
                </div>
                <CardTitle className="text-base mt-2">{test.title}</CardTitle>
                <CardDescription>{test.domain_track}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-slate-600 line-clamp-2">{test.description || 'Evaluation module.'}</p>
                <div className="flex items-center justify-between text-xs text-slate-500 pt-2 border-t border-slate-100">
                  <span>Passing: {test.passing_marks} / {test.total_marks} Marks</span>
                  <span>{test.question_count || 2} Questions</span>
                </div>
                <Button
                  id={`take-test-${test.id}`}
                  onClick={() => startMutation.mutate(test.id)}
                  disabled={startMutation.isPending}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center gap-2 text-xs"
                >
                  <Play className="w-3.5 h-3.5 fill-current" />
                  Take Assessment
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Attempt History Table */}
      <Card>
        <CardHeader>
          <CardTitle>Assessment Attempt History</CardTitle>
          <CardDescription>Verified scores and outcomes evaluated by deterministic grading engine</CardDescription>
        </CardHeader>
        <CardContent>
          {attempts.length === 0 ? (
            <div className="text-center py-8 text-slate-500 text-sm">
              <HelpCircle className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              No assessment attempts taken yet.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4">Test Title</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Attempt #</th>
                    <th className="py-3 px-4">Marks Obtained</th>
                    <th className="py-3 px-4">Percentage</th>
                    <th className="py-3 px-4">Outcome</th>
                    <th className="py-3 px-4">Completed At</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {attempts.map(a => (
                    <tr key={a.id} className="hover:bg-slate-50/50">
                      <td className="py-3 px-4 font-medium text-slate-900">{a.test_title}</td>
                      <td className="py-3 px-4 text-xs">
                        <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700">{a.test_type}</span>
                      </td>
                      <td className="py-3 px-4 font-mono font-semibold">#{a.attempt_number}</td>
                      <td className="py-3 px-4 font-bold text-slate-900">
                        {a.score} / {a.total_marks}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-700">{a.percentage}%</td>
                      <td className="py-3 px-4">
                        <StatusBadge
                          variant={a.passed ? 'success' : 'danger'}
                          label={a.passed ? 'PASSED' : 'FAILED'}
                        />
                      </td>
                      <td className="py-3 px-4 text-xs text-slate-400">
                        {a.completed_at ? new Date(a.completed_at).toLocaleString() : 'In Progress'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Assessment Taking Runner Modal */}
      {runnerOpen && activeTest && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b pb-3">
              <div>
                <h3 className="text-lg font-bold text-slate-900">{activeTest.title}</h3>
                <p className="text-xs text-slate-500">
                  {activeTest.domain_track} • Passing: {activeTest.passing_marks}/{activeTest.total_marks} marks
                </p>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-xs font-semibold">
                <Clock className="w-3.5 h-3.5" />
                {activeTest.duration_minutes} mins allotted
              </div>
            </div>

            {/* Questions List */}
            <div className="space-y-6">
              {(activeTest.questions || []).map((q, idx) => (
                <div key={q.id} className="p-4 bg-slate-50 rounded-lg space-y-3">
                  <div className="flex items-start justify-between">
                    <h4 className="text-sm font-semibold text-slate-900">
                      Q{idx + 1}. {q.question_text}
                    </h4>
                    <span className="text-xs font-medium text-slate-500">{q.marks} Marks</span>
                  </div>

                  <div className="space-y-2">
                    {q.options.map(opt => (
                      <label
                        key={opt.id}
                        className={`flex items-center gap-3 p-2.5 rounded-md border text-sm cursor-pointer transition-colors ${
                          answers[String(q.id)] === opt.id
                            ? 'bg-blue-50 border-blue-600 text-blue-900 font-medium'
                            : 'bg-white border-slate-200 hover:bg-slate-100/50'
                        }`}
                      >
                        <input
                          type="radio"
                          name={`q-${q.id}`}
                          value={opt.id}
                          checked={answers[String(q.id)] === opt.id}
                          onChange={() => setAnswers(prev => ({ ...prev, [String(q.id)]: opt.id }))}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span>{opt.text}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between border-t pt-4">
              <span className="text-xs text-slate-500">
                Answered: {Object.keys(answers).length} of {(activeTest.questions || []).length}
              </span>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setRunnerOpen(false)}>
                  Exit Test
                </Button>
                <Button
                  id="submit-test-btn"
                  onClick={() => submitMutation.mutate()}
                  disabled={submitMutation.isPending}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {submitMutation.isPending ? 'Grading Answers...' : 'Submit Assessment'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Result Outcome Modal */}
      {resultModalOpen && lastResult && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-sm w-full p-6 text-center space-y-4">
            <div
              className={`w-16 h-16 rounded-full mx-auto flex items-center justify-center ${
                lastResult.passed ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'
              }`}
            >
              {lastResult.passed ? <CheckCircle2 className="w-8 h-8" /> : <XCircle className="w-8 h-8" />}
            </div>

            <div>
              <h3 className="text-xl font-bold text-slate-900">
                {lastResult.passed ? 'Assessment Qualified!' : 'Needs Improvement'}
              </h3>
              <p className="text-xs text-slate-500 mt-1">{lastResult.test_title}</p>
            </div>

            <div className="p-4 bg-slate-50 rounded-lg space-y-1">
              <div className="text-3xl font-extrabold text-slate-900">
                {lastResult.score} / {lastResult.total_marks}
              </div>
              <div className="text-sm font-semibold text-slate-600">{lastResult.percentage}% Score</div>
              <div className="text-xs text-slate-400">Passing Threshold: {lastResult.passing_marks} marks</div>
            </div>

            <Button
              onClick={() => setResultModalOpen(false)}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white"
            >
              Close
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
