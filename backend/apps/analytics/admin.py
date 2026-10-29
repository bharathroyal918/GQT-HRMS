"""Django Admin Registration for Continuous Improvement Models (Phase 13)."""
from django.contrib import admin
from apps.analytics.models import (
    CycleImprovementAction,
    RecruitmentCycleReview,
    TrainingPlan,
)


@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "target_skill",
        "target_cohort",
        "responsible_trainer",
        "planned_start_date",
        "planned_end_date",
        "status",
        "approved_by",
    )
    list_filter = ("status", "target_skill", "planned_start_date")
    search_fields = ("title", "target_skill", "target_cohort", "motivation_evidence")
    readonly_fields = ("created_at", "updated_at", "approved_at")


@admin.register(RecruitmentCycleReview)
class RecruitmentCycleReviewAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "cohort_year",
        "review_period_start",
        "review_period_end",
        "status",
        "approved_by",
    )
    list_filter = ("status", "cohort_year")
    search_fields = ("title", "placement_outcomes_summary", "skill_gaps_identified")
    readonly_fields = ("created_at", "updated_at", "approved_at")


@admin.register(CycleImprovementAction)
class CycleImprovementActionAdmin(admin.ModelAdmin):
    list_display = (
        "action_title",
        "cycle_review",
        "category",
        "assigned_to",
        "target_completion_date",
        "status",
    )
    list_filter = ("status", "category", "target_completion_date")
    search_fields = ("action_title", "description", "resolution_notes")
    readonly_fields = ("created_at", "updated_at")
