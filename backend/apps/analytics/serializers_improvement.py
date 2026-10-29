"""Serializers for Continuous Improvement & Strategic Planning (Phase 13)."""
from rest_framework import serializers

from apps.analytics.models import (
    CycleActionCategory,
    CycleActionStatus,
    CycleImprovementAction,
    RecruitmentCycleReview,
    RecruitmentCycleStatus,
    TrainingPlan,
    TrainingPlanStatus,
)


class PlacementRateAnalyticsQuerySerializer(serializers.Serializer):
    cohort_year = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
    department = serializers.CharField(required=False, allow_blank=True)
    college_name = serializers.CharField(required=False, allow_blank=True)
    company_id = serializers.UUIDField(required=False)
    job_requirement_id = serializers.UUIDField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class FeedbackIntelligenceQuerySerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False)
    job_requirement_id = serializers.UUIDField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    cohort_year = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
    department = serializers.CharField(required=False, allow_blank=True)


class SkillGapMatrixQuerySerializer(serializers.Serializer):
    company_id = serializers.UUIDField(required=False)
    cohort_year = serializers.IntegerField(required=False, min_value=2000, max_value=2100)
    department = serializers.CharField(required=False, allow_blank=True)


class TrainingPlanCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    target_skill = serializers.CharField(max_length=100)
    motivation_evidence = serializers.CharField()
    target_cohort = serializers.CharField(max_length=255)
    proposed_objectives = serializers.CharField()
    planned_sessions_count = serializers.IntegerField(min_value=1, default=1)
    responsible_trainer_id = serializers.UUIDField(required=False)
    planned_start_date = serializers.DateField()
    planned_end_date = serializers.DateField()
    expected_outcome = serializers.CharField()
    status = serializers.ChoiceField(
        choices=TrainingPlanStatus.CHOICES,
        default=TrainingPlanStatus.DRAFT,
    )


class TrainingPlanStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=TrainingPlanStatus.CHOICES, required=False)
    status = serializers.ChoiceField(choices=TrainingPlanStatus.CHOICES, required=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    actual_results = serializers.CharField(required=False, allow_blank=True, default="")
    cancellation_reason = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        status_val = attrs.get("new_status") or attrs.get("status")
        if not status_val:
            raise serializers.ValidationError({"new_status": "This field is required."})
        attrs["new_status"] = status_val
        return attrs


class RecruitmentCycleReviewCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    cohort_year = serializers.IntegerField(min_value=2000, max_value=2100)
    review_period_start = serializers.DateField()
    review_period_end = serializers.DateField()
    target_goals = serializers.DictField(required=False, default=dict)
    placement_outcomes_summary = serializers.CharField(required=False, allow_blank=True, default="")
    feedback_summary = serializers.CharField(required=False, allow_blank=True, default="")
    skill_gaps_identified = serializers.CharField(required=False, allow_blank=True, default="")


class RecruitmentCycleStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=RecruitmentCycleStatus.CHOICES)


class CycleImprovementActionCreateSerializer(serializers.Serializer):
    action_title = serializers.CharField(max_length=255)
    category = serializers.ChoiceField(
        choices=CycleActionCategory.CHOICES,
        default=CycleActionCategory.REMEDIAL_TRAINING,
    )
    description = serializers.CharField()
    target_completion_date = serializers.DateField()
    assigned_to_id = serializers.UUIDField(required=False, allow_null=True)
    linked_training_plan_id = serializers.UUIDField(required=False, allow_null=True)


class CycleImprovementActionStatusUpdateSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(choices=CycleActionStatus.CHOICES, required=False)
    status = serializers.ChoiceField(choices=CycleActionStatus.CHOICES, required=False)
    resolution_notes = serializers.CharField(required=False, allow_blank=True, default="")
    outcome_notes = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        status_val = attrs.get("new_status") or attrs.get("status")
        if not status_val:
            raise serializers.ValidationError({"new_status": "This field is required."})
        attrs["new_status"] = status_val
        notes = attrs.get("resolution_notes") or attrs.get("outcome_notes", "")
        attrs["resolution_notes"] = notes
        return attrs
