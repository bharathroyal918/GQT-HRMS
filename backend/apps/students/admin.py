"""Django Admin site registration for Students and Eligibility Engine models."""
from django.contrib import admin
from apps.students.models import (
    JobPublication,
    StudentProfile,
    StudentResume,
    StudentApplication,
    EligibilityEvaluation,
    CandidateCohort,
    CohortMember,
)


@admin.register(JobPublication)
class JobPublicationAdmin(admin.ModelAdmin):
    list_display = ("job_requirement", "channel", "status", "target_audience", "dispatched_at", "delivered_at")
    list_filter = ("channel", "status")
    search_fields = ("job_requirement__title", "subject", "target_audience")


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("roll_number", "institutional_email", "degree", "department", "graduation_year", "cgpa", "active_backlogs", "is_verified_by_placement")
    list_filter = ("department", "graduation_year", "is_verified_by_placement")
    search_fields = ("roll_number", "institutional_email", "user__first_name", "user__last_name")


@admin.register(StudentResume)
class StudentResumeAdmin(admin.ModelAdmin):
    list_display = ("student", "version_number", "file_name", "file_size_bytes", "is_current", "created_at")
    list_filter = ("is_current",)
    search_fields = ("student__roll_number", "file_name", "sha256_hash")


@admin.register(StudentApplication)
class StudentApplicationAdmin(admin.ModelAdmin):
    list_display = ("student", "job_requirement", "status", "applied_at")
    list_filter = ("status",)
    search_fields = ("student__roll_number", "job_requirement__title")


@admin.register(EligibilityEvaluation)
class EligibilityEvaluationAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "is_overridden", "override_by", "evaluated_at")
    list_filter = ("status", "is_overridden")
    search_fields = ("application__student__roll_number", "application__job_requirement__title")


@admin.register(CandidateCohort)
class CandidateCohortAdmin(admin.ModelAdmin):
    list_display = ("title", "job_requirement", "is_locked", "finalized_by", "finalized_at")
    list_filter = ("is_locked",)
    search_fields = ("title", "job_requirement__title")


@admin.register(CohortMember)
class CohortMemberAdmin(admin.ModelAdmin):
    list_display = ("cohort", "student", "is_eligible", "is_override", "override_by")
    list_filter = ("is_eligible", "is_override")
    search_fields = ("student__roll_number", "cohort__title")
