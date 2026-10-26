import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Upload,
  Search,
  Star,
  UserCheck,
} from 'lucide-react';
import { preparationApi } from '@/api/preparationApi';
import { useAuth } from '@/context/AuthContext';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '@/components/common/Card';
import { Button } from '@/components/common/Button';
import { StatusBadge } from '@/components/common/StatusBadge';
import { LoadingState } from '@/components/common/LoadingState';
import { ErrorState } from '@/components/common/ErrorState';
import { ResumeReview } from '@/types/preparation';

export const ResumeReviewWorkspacePage: React.FC = () => {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const userRoles = user?.roles || [];
  const isTrainerOrStaff =
    user?.is_superuser ||
    userRoles.some(r => ['TRAINER', 'PLACEMENT_OFFICER', 'PLACEMENT_HEAD', 'ADMIN'].includes(r));
  const isStudent = userRoles.includes('STUDENT');

  const [selectedReview, setSelectedReview] = useState<ResumeReview | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  // Review Form State
  const [targetResumeId, setTargetResumeId] = useState('');
  const [reviewStatus, setReviewStatus] = useState<'APPROVED' | 'REVISION_REQUESTED'>('APPROVED');
  const [formattingScore, setFormattingScore] = useState(8);
  const [technicalScore, setTechnicalScore] = useState(8);
  const [projectsScore, setProjectsScore] = useState(8);
  const [achievementsScore, setAchievementsScore] = useState(8);
  const [detailedFeedback, setDetailedFeedback] = useState('');
  const [suggestedImprovements, setSuggestedImprovements] = useState('');
  const [reviewError, setReviewError] = useState<string | null>(null);

  // Student Re-upload State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [studentNotes, setStudentNotes] = useState('');
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Fetch reviews
  const {
    data: reviews = [],
    isLoading: reviewsLoading,
    error: reviewsError,
  } = useQuery({
    queryKey: ['preparation-resume-reviews'],
    queryFn: () => preparationApi.listResumeReviews(),
  });

  // Fetch improvement cycles
  const {
    data: cycles = [],
    isLoading: cyclesLoading,
  } = useQuery({
    queryKey: ['preparation-improvement-cycles'],
    queryFn: () => preparationApi.listImprovementCycles(),
  });

  // Review submission mutation
  const reviewMutation = useMutation({
    mutationFn: () =>
      preparationApi.submitResumeReview({
        resume_id: targetResumeId,
        status: reviewStatus,
        formatting_score: formattingScore,
        technical_skills_score: technicalScore,
        projects_score: projectsScore,
        achievements_score: achievementsScore,
        detailed_feedback: detailedFeedback,
        suggested_improvements: suggestedImprovements,
      }),
    onSuccess: () => {
      setReviewModalOpen(false);
      setReviewError(null);
      setDetailedFeedback('');
      setSuggestedImprovements('');
      queryClient.invalidateQueries({ queryKey: ['preparation-resume-reviews'] });
      queryClient.invalidateQueries({ queryKey: ['preparation-improvement-cycles'] });
    },
    onError: (err: any) => {
      setReviewError(err.response?.data?.detail || err.message || 'Failed to submit review.');
    },
  });

  // Improved resume re-upload mutation
  const uploadMutation = useMutation({
    mutationFn: () => preparationApi.submitImprovedResume(uploadFile!, studentNotes),
    onSuccess: () => {
      setUploadModalOpen(false);
      setUploadFile(null);
      setStudentNotes('');
      setUploadError(null);
      queryClient.invalidateQueries({ queryKey: ['preparation-resume-reviews'] });
      queryClient.invalidateQueries({ queryKey: ['preparation-improvement-cycles'] });
    },
    onError: (err: any) => {
      setUploadError(err.response?.data?.detail || err.message || 'Failed to re-upload resume.');
    },
  });

  if (reviewsLoading || cyclesLoading) {
    return <LoadingState message="Loading resume reviews and improvement cycles..." />;
  }

  if (reviewsError) {
    return <ErrorState message="Failed to load resume review workspace." />;
  }

  const approvedCount = reviews.filter(r => r.status === 'APPROVED').length;
  const revisionCount = reviews.filter(r => r.status === 'REVISION_REQUESTED').length;
  const filteredReviews = reviews.filter(
    r =>
      r.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.student_roll_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Resume Review & Improvement Cycle
          </h1>
          <p className="text-sm text-slate-500">
            Workflow Steps 15–16: Institutional Rubric Evaluation & Iterative Monotonic Resumes
          </p>
        </div>
        <div className="flex gap-2">
          {isStudent && (
            <Button
              id="upload-improved-resume-btn"
              onClick={() => setUploadModalOpen(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Upload Revised Resume (v2+)
            </Button>
          )}
          {isTrainerOrStaff && (
            <Button
              id="new-resume-review-btn"
              onClick={() => {
                setTargetResumeId(reviews[0]?.resume || '');
                setReviewModalOpen(true);
              }}
              className="bg-slate-900 hover:bg-slate-800 text-white flex items-center gap-2"
            >
              <Star className="w-4 h-4" />
              Conduct Rubric Review
            </Button>
          )}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Evaluations</p>
                <h3 className="text-2xl font-bold text-slate-900 mt-1">{reviews.length}</h3>
              </div>
              <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                <FileText className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Trainer Approved</p>
                <h3 className="text-2xl font-bold text-emerald-600 mt-1">{approvedCount}</h3>
              </div>
              <div className="p-3 bg-emerald-50 text-emerald-600 rounded-lg">
                <CheckCircle2 className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Revisions Requested</p>
                <h3 className="text-2xl font-bold text-amber-600 mt-1">{revisionCount}</h3>
              </div>
              <div className="p-3 bg-amber-50 text-amber-600 rounded-lg">
                <AlertTriangle className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Improvement Cycles</p>
                <h3 className="text-2xl font-bold text-indigo-600 mt-1">{cycles.length}</h3>
              </div>
              <div className="p-3 bg-indigo-50 text-indigo-600 rounded-lg">
                <RotateCcw className="w-6 h-6" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Workspace Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reviews Table (2 cols) */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <CardTitle>Resume Review History (Step 15)</CardTitle>
                  <CardDescription>Rubric ratings across formatting, technical skills, and projects</CardDescription>
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
              {filteredReviews.length === 0 ? (
                <div className="text-center py-12 text-slate-500">
                  <FileText className="w-12 h-12 mx-auto text-slate-300 mb-2" />
                  <p>No resume reviews recorded yet.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm text-slate-600">
                    <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
                      <tr>
                        <th className="py-3 px-4">Candidate</th>
                        <th className="py-3 px-4">Resume Version</th>
                        <th className="py-3 px-4">Decision</th>
                        <th className="py-3 px-4">Score (40)</th>
                        <th className="py-3 px-4">Reviewer</th>
                        <th className="py-3 px-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {filteredReviews.map(r => (
                        <tr key={r.id} className="hover:bg-slate-50/50 transition-colors">
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-900">{r.student_name}</div>
                            <div className="text-xs text-slate-400">{r.student_roll_number}</div>
                          </td>
                          <td className="py-3 px-4 font-mono font-semibold text-slate-700">
                            v{r.resume_version}
                          </td>
                          <td className="py-3 px-4">
                            <StatusBadge
                              variant={r.status === 'APPROVED' ? 'success' : 'warning'}
                              label={r.status === 'APPROVED' ? 'Approved' : 'Revision Requested'}
                            />
                          </td>
                          <td className="py-3 px-4">
                            <span className="inline-flex items-center gap-1 font-semibold text-slate-900">
                              <Star className="w-3.5 h-3.5 text-amber-500 fill-amber-500" />
                              {r.aggregate_score} / 40
                            </span>
                          </td>
                          <td className="py-3 px-4 text-xs text-slate-500">{r.reviewer_name}</td>
                          <td className="py-3 px-4 text-right">
                            <button
                              onClick={() => setSelectedReview(r)}
                              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              Inspect Rubric
                            </button>
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

        {/* Selected Review Detail / Improvement Cycles (1 col) */}
        <div className="space-y-6">
          {selectedReview ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Rubric Evaluation Detail</CardTitle>
                  <StatusBadge
                    variant={selectedReview.status === 'APPROVED' ? 'success' : 'warning'}
                    label={selectedReview.status === 'APPROVED' ? 'Approved' : 'Revision Requested'}
                  />
                </div>
                <CardDescription>
                  {selectedReview.student_name} ({selectedReview.student_roll_number}) • Resume v
                  {selectedReview.resume_version}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Formatting</p>
                    <p className="font-bold text-slate-900">{selectedReview.formatting_score} / 10</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Technical Skills</p>
                    <p className="font-bold text-slate-900">{selectedReview.technical_skills_score} / 10</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Projects & Experience</p>
                    <p className="font-bold text-slate-900">{selectedReview.projects_score} / 10</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500">Achievements</p>
                    <p className="font-bold text-slate-900">{selectedReview.achievements_score} / 10</p>
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                    Trainer Feedback
                  </h4>
                  <p className="text-sm text-slate-800 p-3 bg-slate-50 rounded-lg whitespace-pre-wrap">
                    {selectedReview.detailed_feedback}
                  </p>
                </div>

                {selectedReview.suggested_improvements && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">
                      Actionable Improvements
                    </h4>
                    <p className="text-sm text-slate-700 p-3 bg-amber-50/50 border border-amber-200/50 rounded-lg whitespace-pre-wrap">
                      {selectedReview.suggested_improvements}
                    </p>
                  </div>
                )}

                <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span>Evaluator: {selectedReview.reviewer_name}</span>
                  <span>{new Date(selectedReview.reviewed_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6 text-center text-slate-500">
                <UserCheck className="w-10 h-10 mx-auto text-slate-300 mb-2" />
                <p className="text-sm">Select any review from the table to inspect rubric scores and feedback.</p>
              </CardContent>
            </Card>
          )}

          {/* Active Improvement Cycles Card */}
          <Card>
            <CardHeader>
              <CardTitle>Improvement Cycles (Step 16)</CardTitle>
              <CardDescription>Tracks revisions addressing trainer feedback</CardDescription>
            </CardHeader>
            <CardContent>
              {cycles.length === 0 ? (
                <p className="text-xs text-slate-500 text-center py-4">No active revision cycles.</p>
              ) : (
                <div className="space-y-3">
                  {cycles.slice(0, 5).map(c => (
                    <div key={c.id} className="p-3 border border-slate-100 rounded-lg text-xs space-y-1">
                      <div className="flex items-center justify-between font-semibold text-slate-900">
                        <span>{c.student_name}</span>
                        <StatusBadge
                          variant={c.status === 'REVISED_UPLOADED' ? 'info' : c.status === 'RE_REVIEWED' ? 'success' : 'warning'}
                          label={c.status === 'REVISED_UPLOADED' ? 'Revised Uploaded' : c.status === 'RE_REVIEWED' ? 'Re-reviewed' : 'Revision Pending'}
                        />
                      </div>
                      <div className="text-slate-500">
                        Transition: v{c.prior_resume_version} →{' '}
                        {c.improved_resume_version ? `v${c.improved_resume_version}` : 'Pending re-upload'}
                      </div>
                      {c.student_notes && (
                        <div className="text-slate-600 italic">Notes: {c.student_notes}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Trainer Review Modal */}
      {reviewModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-lg w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Conduct Resume Rubric Review (Step 15)</h3>

            {reviewError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg">
                {reviewError}
              </div>
            )}

            <div className="space-y-3 text-sm">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Target Resume UUID</label>
                <input
                  type="text"
                  value={targetResumeId}
                  onChange={e => setTargetResumeId(e.target.value)}
                  placeholder="Resume UUID"
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Review Outcome</label>
                <select
                  value={reviewStatus}
                  onChange={e => setReviewStatus(e.target.value as any)}
                  className="w-full px-3 py-2 border rounded-md"
                >
                  <option value="APPROVED">APPROVED (Meets Institutional Standards)</option>
                  <option value="REVISION_REQUESTED">REVISION_REQUESTED (Requires Candidate Improvement)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Formatting (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={formattingScore}
                    onChange={e => setFormattingScore(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Technical Skills (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={technicalScore}
                    onChange={e => setTechnicalScore(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Projects (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={projectsScore}
                    onChange={e => setProjectsScore(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600 mb-1">Achievements (1-10)</label>
                  <input
                    type="number"
                    min={1}
                    max={10}
                    value={achievementsScore}
                    onChange={e => setAchievementsScore(Number(e.target.value))}
                    className="w-full px-3 py-2 border rounded-md"
                  />
                </div>
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Detailed Evaluation Comments</label>
                <textarea
                  rows={3}
                  value={detailedFeedback}
                  onChange={e => setDetailedFeedback(e.target.value)}
                  placeholder="Provide structured feedback covering strengths and weaknesses..."
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Suggested Revisions (Optional)</label>
                <textarea
                  rows={2}
                  value={suggestedImprovements}
                  onChange={e => setSuggestedImprovements(e.target.value)}
                  placeholder="Specific actions candidate should take..."
                  className="w-full px-3 py-2 border rounded-md"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setReviewModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => reviewMutation.mutate()}
                disabled={reviewMutation.isPending || !detailedFeedback.trim()}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {reviewMutation.isPending ? 'Submitting...' : 'Submit Rubric Review'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Student Re-upload Modal */}
      {uploadModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 space-y-4">
            <h3 className="text-lg font-bold text-slate-900">Upload Improved Resume (Step 16)</h3>
            <p className="text-xs text-slate-500">
              Upload your revised PDF addressing trainer review recommendations. This automatically creates a monotonic version (v2+).
            </p>

            {uploadError && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg">
                {uploadError}
              </div>
            )}

            <div className="space-y-3 text-sm">
              <div>
                <label className="block font-medium text-slate-700 mb-1">Select Resume PDF</label>
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={e => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs"
                />
              </div>

              <div>
                <label className="block font-medium text-slate-700 mb-1">Summary of Improvements</label>
                <textarea
                  rows={3}
                  value={studentNotes}
                  onChange={e => setStudentNotes(e.target.value)}
                  placeholder="Briefly state what changes were made in this iteration..."
                  className="w-full px-3 py-2 border rounded-md text-xs"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" onClick={() => setUploadModalOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={() => uploadMutation.mutate()}
                disabled={uploadMutation.isPending || !uploadFile}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {uploadMutation.isPending ? 'Uploading...' : 'Submit Revision'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
