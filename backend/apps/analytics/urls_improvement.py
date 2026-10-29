"""URL Routing for Continuous Improvement & Strategic Planning (Phase 13).

Mounted under: /api/v1/continuous-improvement/
"""
from django.urls import path

from apps.analytics.views_improvement import (
    ContinuousImprovementDiagnosticsView,
    CycleImprovementActionCreateView,
    CycleImprovementActionStatusUpdateView,
    FeedbackIntelligenceView,
    PlacementRateAnalyticsExportView,
    PlacementRateAnalyticsView,
    RecruitmentCycleReviewDetailView,
    RecruitmentCycleReviewListCreateView,
    RecruitmentCycleStatusUpdateView,
    SkillGapMatrixExportView,
    SkillGapMatrixView,
    TrainingPlanDetailView,
    TrainingPlanExportView,
    TrainingPlanListCreateView,
    TrainingPlanStatusUpdateView,
)

app_name = "continuous_improvement"

urlpatterns = [
    # Capability A: Placement Rate Analytics & Export
    path("placement-rate/", PlacementRateAnalyticsView.as_view(), name="placement-rate-analytics"),
    path("placement-rate/export/", PlacementRateAnalyticsExportView.as_view(), name="placement-rate-export"),

    # Capability B: Feedback Intelligence
    path("feedback/", FeedbackIntelligenceView.as_view(), name="feedback-intelligence"),
    path("feedback-intelligence/", FeedbackIntelligenceView.as_view(), name="feedback-intelligence-alias"),

    # Capability C: Skill Gap Matrix & Export
    path("skill-gaps/", SkillGapMatrixView.as_view(), name="skill-gap-matrix"),
    path("skill-gap-matrix/", SkillGapMatrixView.as_view(), name="skill-gap-matrix-alias"),
    path("skill-gaps/export/", SkillGapMatrixExportView.as_view(), name="skill-gap-matrix-export"),
    path("skill-gap-matrix/export/", SkillGapMatrixExportView.as_view(), name="skill-gap-matrix-export-alias"),

    # Capability D: Strategic Training Plans
    path("training-plans/", TrainingPlanListCreateView.as_view(), name="training-plans-list-create"),
    path("training-plans/export/", TrainingPlanExportView.as_view(), name="training-plans-export"),
    path("training-plans/<str:plan_id>/", TrainingPlanDetailView.as_view(), name="training-plan-detail"),
    path("training-plans/<str:plan_id>/status/", TrainingPlanStatusUpdateView.as_view(), name="training-plan-status-update"),
    path("training-plans/<str:plan_id>/transition/", TrainingPlanStatusUpdateView.as_view(), name="training-plan-transition-alias"),

    # Capability E: Recruitment Cycle Reviews & Actions
    path("cycle-reviews/", RecruitmentCycleReviewListCreateView.as_view(), name="cycle-reviews-list-create"),
    path("recruitment-cycles/", RecruitmentCycleReviewListCreateView.as_view(), name="recruitment-cycles-alias"),
    path("cycle-reviews/<str:review_id>/", RecruitmentCycleReviewDetailView.as_view(), name="cycle-review-detail"),
    path("recruitment-cycles/<str:review_id>/", RecruitmentCycleReviewDetailView.as_view(), name="recruitment-cycle-detail-alias"),
    path("cycle-reviews/<str:review_id>/status/", RecruitmentCycleStatusUpdateView.as_view(), name="cycle-review-status-update"),
    path("recruitment-cycles/<str:review_id>/status/", RecruitmentCycleStatusUpdateView.as_view(), name="recruitment-cycle-status-alias"),
    path("cycle-reviews/<str:review_id>/actions/", CycleImprovementActionCreateView.as_view(), name="cycle-action-create"),
    path("cycle-actions/", CycleImprovementActionCreateView.as_view(), name="cycle-action-create-direct"),
    path("cycle-actions/<str:action_id>/status/", CycleImprovementActionStatusUpdateView.as_view(), name="cycle-action-status-update"),
    path("cycle-actions/<str:action_id>/", CycleImprovementActionStatusUpdateView.as_view(), name="cycle-action-alias"),

    # Diagnostics: Continuous Improvement Health Scan
    path("diagnostics/", ContinuousImprovementDiagnosticsView.as_view(), name="improvement-diagnostics"),
]
