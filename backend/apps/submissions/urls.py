"""URL Configuration for Candidate Submissions & Profile Dispatch API (Phase 7)."""
from django.urls import path
from apps.submissions.views import (
    JobEligibleCandidatesAPIView,
    SubmissionPackageListCreateAPIView,
    SubmissionPackageDetailAPIView,
    SubmissionPackageGenerateRosterAPIView,
    SubmissionPackageDownloadRosterAPIView,
    SubmissionPackageAttachResumesAPIView,
    SubmissionPackageDispatchAPIView,
    SubmissionPackageAcknowledgeAPIView,
    StudentSubmissionsListAPIView,
)

app_name = "submissions"

urlpatterns = [
    # Step 24: Candidate preparation & Package creation
    path("jobs/<uuid:job_id>/candidates/", JobEligibleCandidatesAPIView.as_view(), name="job-candidates"),
    path("packages/", SubmissionPackageListCreateAPIView.as_view(), name="package-list-create"),
    path("packages/<uuid:package_id>/", SubmissionPackageDetailAPIView.as_view(), name="package-detail"),

    # Step 25: Master Excel Spreadsheet generation & download
    path("packages/<uuid:package_id>/roster/generate/", SubmissionPackageGenerateRosterAPIView.as_view(), name="package-roster-generate"),
    path("packages/<uuid:package_id>/roster/download/", SubmissionPackageDownloadRosterAPIView.as_view(), name="package-roster-download"),

    # Step 26: Resume attachments verification
    path("packages/<uuid:package_id>/resumes/attach/", SubmissionPackageAttachResumesAPIView.as_view(), name="package-attach-resumes"),

    # Step 27: Profile Dispatch to Corporate HR
    path("packages/<uuid:package_id>/dispatch/", SubmissionPackageDispatchAPIView.as_view(), name="package-dispatch"),

    # Step 28: Recruiter Acknowledgment
    path("packages/<uuid:package_id>/acknowledge/", SubmissionPackageAcknowledgeAPIView.as_view(), name="package-acknowledge"),

    # Candidate self-service submission tracking
    path("my-submissions/", StudentSubmissionsListAPIView.as_view(), name="student-submissions"),
]
