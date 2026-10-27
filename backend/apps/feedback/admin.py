"""Admin registrations for Phase 9 Feedback Collection."""
from django.contrib import admin
from apps.feedback.models import HRFeedback, StudentFeedback, TrainerFeedback


@admin.register(StudentFeedback)
class StudentFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "company",
        "job_requirement",
        "difficulty",
        "is_anonymous",
        "submitted_by",
        "created_at",
    )
    list_filter = ("difficulty", "is_anonymous", "company", "created_at")
    search_fields = (
        "student__roll_number",
        "student__user__first_name",
        "student__user__last_name",
        "company__name",
        "technical_questions",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(HRFeedback)
class HRFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "company",
        "candidate",
        "candidate_quality",
        "technical_skills_rating",
        "communication_skills_rating",
        "hiring_satisfaction_rating",
        "submitted_by",
        "created_at",
    )
    list_filter = (
        "candidate_quality",
        "technical_skills_rating",
        "communication_skills_rating",
        "hiring_satisfaction_rating",
        "company",
        "created_at",
    )
    search_fields = (
        "company__name",
        "candidate__roll_number",
        "candidate__user__first_name",
        "candidate__user__last_name",
        "candidate_quality_remarks",
        "hiring_satisfaction_remarks",
    )
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TrainerFeedback)
class TrainerFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "student",
        "training_session",
        "student_readiness",
        "training_effectiveness_rating",
        "trainer",
        "created_at",
    )
    list_filter = (
        "student_readiness",
        "training_effectiveness_rating",
        "created_at",
    )
    search_fields = (
        "student__roll_number",
        "student__user__first_name",
        "student__user__last_name",
        "trainer__first_name",
        "trainer__last_name",
        "areas_for_improvement",
    )
    readonly_fields = ("id", "created_at", "updated_at")
