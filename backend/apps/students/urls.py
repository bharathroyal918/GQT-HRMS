"""URL routing configuration for the Students and Eligibility Engine domain."""
from django.urls import path
from apps.students.views import (
    JobPublicationListCreateAPIView,
    JobPublicationRetryAPIView,
    EligibleJobPublicationListAPIView,
    JobEligibilityPreviewAPIView,
    StudentRegistrationAPIView,
    StudentProfileMeAPIView,
    StudentProfileDetailAPIView,
    StudentProfileListAPIView,
    StudentResumeUploadAPIView,
    StudentResumeDownloadAPIView,
    StudentApplicationApplyAPIView,
    StudentApplicationListAPIView,
    EligibilityEvaluationDetailAPIView,
    EligibilityOverrideAPIView,
    CandidateCohortDetailAPIView,
    CandidateCohortFinalizeAPIView,
)

app_name = "students"

urlpatterns = [
    # Step 10: Publish Job Notification & Eligible Drives Discovery
    path("publications/", JobPublicationListCreateAPIView.as_view(), name="publication-list-create"),
    path("publications/eligible/", EligibleJobPublicationListAPIView.as_view(), name="publication-eligible-list"),
    path("publications/<uuid:pub_id>/retry/", JobPublicationRetryAPIView.as_view(), name="publication-retry"),
    path("jobs/<uuid:job_id>/eligibility-preview/", JobEligibilityPreviewAPIView.as_view(), name="job-eligibility-preview"),
    path("eligibility/preview/", JobEligibilityPreviewAPIView.as_view(), name="eligibility-preview"),

    # Step 11: Student Registration
    path("register/", StudentRegistrationAPIView.as_view(), name="student-register"),

    # Step 12: Collect Student Profile & Resume
    path("profile/me/", StudentProfileMeAPIView.as_view(), name="profile-me"),
    path("profile/<uuid:profile_id>/", StudentProfileDetailAPIView.as_view(), name="profile-detail"),
    path("profiles/", StudentProfileListAPIView.as_view(), name="profile-list"),
    path("resumes/upload/", StudentResumeUploadAPIView.as_view(), name="resume-upload"),
    path("resumes/<uuid:resume_id>/download/", StudentResumeDownloadAPIView.as_view(), name="resume-download"),

    # Step 13: Eligibility Verification Engine & Applications
    path("applications/apply/", StudentApplicationApplyAPIView.as_view(), name="application-apply"),
    path("applications/", StudentApplicationListAPIView.as_view(), name="application-list"),
    path("eligibility/<uuid:eval_id>/", EligibilityEvaluationDetailAPIView.as_view(), name="eligibility-detail"),

    # Step 14: Eligible Candidate Cohort Finalization & Manual Overrides
    path("eligibility/<uuid:eval_id>/override/", EligibilityOverrideAPIView.as_view(), name="eligibility-override"),
    path("cohorts/<uuid:job_id>/", CandidateCohortDetailAPIView.as_view(), name="cohort-detail"),
    path("cohorts/<uuid:job_id>/finalize/", CandidateCohortFinalizeAPIView.as_view(), name="cohort-finalize"),
]
