"""URL Routing Configuration for Student Preparation (Phase 6 / Steps 15-23)."""
from django.urls import path
from apps.preparation.views import (
    ResumeReviewListCreateView,
    ResumeImprovementCycleListView,
    ResumeImprovementSubmitView,
    AssessmentTestListView,
    AssessmentTestDetailView,
    AssessmentAttemptStartView,
    AssessmentAttemptSubmitView,
    AssessmentAttemptListView,
    TrainingSessionListView,
    TrainingAttendanceListView,
    RecordTrainingAttendanceView,
    MockInterviewListCreateView,
    MockInterviewEvaluateView,
    PlacementReadinessSnapshotView,
    PlacementReadinessCertificationListView,
    CertifyPlacementReadinessView,
)

app_name = "preparation"

urlpatterns = [
    # Step 15: Resume Review
    path("resume-reviews/", ResumeReviewListCreateView.as_view(), name="resume-reviews"),

    # Step 16: Resume Improvement
    path("improvement-cycles/", ResumeImprovementCycleListView.as_view(), name="improvement-cycles"),
    path("improvement-cycles/submit/", ResumeImprovementSubmitView.as_view(), name="improvement-submit"),

    # Steps 17 & 18: Aptitude & Technical Assessments
    path("tests/", AssessmentTestListView.as_view(), name="tests-list"),
    path("tests/<uuid:pk>/", AssessmentTestDetailView.as_view(), name="test-detail"),
    path("attempts/", AssessmentAttemptListView.as_view(), name="attempts-list"),
    path("attempts/start/", AssessmentAttemptStartView.as_view(), name="attempt-start"),
    path("attempts/submit/", AssessmentAttemptSubmitView.as_view(), name="attempt-submit"),

    # Steps 19 & 20: Communication & Grooming Sessions
    path("sessions/", TrainingSessionListView.as_view(), name="sessions-list"),
    path("attendances/", TrainingAttendanceListView.as_view(), name="attendances-list"),
    path("attendances/record/", RecordTrainingAttendanceView.as_view(), name="attendance-record"),

    # Steps 21 & 22: Mock Interviews & Rubric Evaluations
    path("mock-interviews/", MockInterviewListCreateView.as_view(), name="mock-interviews"),
    path("mock-interviews/evaluate/", MockInterviewEvaluateView.as_view(), name="mock-evaluate"),

    # Step 23: Placement Readiness Certification Gate
    path("readiness-snapshot/<uuid:student_id>/", PlacementReadinessSnapshotView.as_view(), name="readiness-snapshot"),
    path("certifications/", PlacementReadinessCertificationListView.as_view(), name="certifications-list"),
    path("certifications/certify/", CertifyPlacementReadinessView.as_view(), name="certify-readiness"),
]
