"""Django Admin Registration for Candidate Submissions & Profile Dispatch (Phase 7)."""
from django.contrib import admin
from apps.submissions.models import SubmissionPackage, CandidateSubmission, SubmissionDispatchLog


class CandidateSubmissionInline(admin.TabularInline):
    model = CandidateSubmission
    extra = 0
    readonly_fields = ("student", "application", "readiness_certification", "submitted_resume", "resume_version_number", "resume_sha256", "status", "created_at")
    can_delete = False


class SubmissionDispatchLogInline(admin.TabularInline):
    model = SubmissionDispatchLog
    extra = 0
    readonly_fields = ("attempt_number", "channel", "recipient", "status", "provider_message_id", "timestamp")
    can_delete = False


@admin.register(SubmissionPackage)
class SubmissionPackageAdmin(admin.ModelAdmin):
    list_display = ("title", "job_requirement", "company", "status", "candidate_count", "dispatched_at", "acknowledged_at")
    list_filter = ("status", "dispatch_channel", "created_at")
    search_fields = ("title", "company__name", "job_requirement__title", "recipient_email", "provider_reference")
    readonly_fields = ("package_hash", "roster_generated_at", "resumes_attached_at", "created_at", "updated_at")
    inlines = [CandidateSubmissionInline, SubmissionDispatchLogInline]


@admin.register(CandidateSubmission)
class CandidateSubmissionAdmin(admin.ModelAdmin):
    list_display = ("student", "package", "resume_version_number", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("student__roll_number", "student__user__email", "package__title")


@admin.register(SubmissionDispatchLog)
class SubmissionDispatchLogAdmin(admin.ModelAdmin):
    list_display = ("package", "attempt_number", "channel", "recipient", "status", "timestamp")
    list_filter = ("channel", "status", "timestamp")
