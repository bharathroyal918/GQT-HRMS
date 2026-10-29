"""Views for Continuous Improvement & Strategic Planning (Phase 13).

Mounted under: /api/v1/continuous-improvement/
"""
from django.core.exceptions import (
    PermissionDenied as DjangoPermissionDenied,
    ValidationError as DjangoValidationError,
)
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied as DRFPermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.models import (
    CycleImprovementAction,
    RecruitmentCycleReview,
    TrainingPlan,
)
from apps.analytics.permissions import (
    CanAccessFeedbackIntelligence,
    CanAccessPlacementRateAnalytics,
    CanAccessSkillGapMatrix,
    CanManageCycleReviews,
    CanManageTrainingPlans,
)
from apps.analytics.selectors_improvement import (
    get_continuous_improvement_diagnostics,
    get_feedback_intelligence,
    get_placement_rate_analytics,
    get_recruitment_cycle_reviews_dataset,
    get_skill_gap_analysis,
    get_training_plans_dataset,
)
from apps.analytics.serializers_improvement import (
    CycleImprovementActionCreateSerializer,
    CycleImprovementActionStatusUpdateSerializer,
    FeedbackIntelligenceQuerySerializer,
    PlacementRateAnalyticsQuerySerializer,
    RecruitmentCycleReviewCreateSerializer,
    RecruitmentCycleStatusUpdateSerializer,
    SkillGapMatrixQuerySerializer,
    TrainingPlanCreateSerializer,
    TrainingPlanStatusUpdateSerializer,
)
from apps.analytics.services_improvement import (
    create_cycle_improvement_action,
    create_recruitment_cycle_review,
    create_training_plan,
    export_placement_rate_csv,
    export_skill_gaps_csv,
    export_training_plans_csv,
    update_cycle_improvement_action_status,
    update_recruitment_cycle_status,
    update_training_plan_status,
)


class PlacementRateAnalyticsView(APIView):
    """Capability A: Granular Placement Rate Analytics."""

    permission_classes = [IsAuthenticated, CanAccessPlacementRateAnalytics]

    def get(self, request):
        query_serializer = PlacementRateAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        dataset = get_placement_rate_analytics(
            filters=query_serializer.validated_data,
            user=request.user,
        )
        return Response(dataset, status=status.HTTP_200_OK)


class PlacementRateAnalyticsExportView(APIView):
    """Capability A: Export Placement Rate Analytics as Safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessPlacementRateAnalytics]

    def get(self, request):
        query_serializer = PlacementRateAnalyticsQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        dataset = get_placement_rate_analytics(
            filters=query_serializer.validated_data,
            user=request.user,
        )
        csv_content = export_placement_rate_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="placement_rate_analytics.csv"'
        return response


class FeedbackIntelligenceView(APIView):
    """Capability B: Cross-Category Feedback Intelligence."""

    permission_classes = [IsAuthenticated, CanAccessFeedbackIntelligence]

    def get(self, request):
        query_serializer = FeedbackIntelligenceQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        dataset = get_feedback_intelligence(
            filters=query_serializer.validated_data,
            user=request.user,
        )
        if "error" in dataset:
            return Response(dataset, status=status.HTTP_403_FORBIDDEN)
        return Response(dataset, status=status.HTTP_200_OK)


class SkillGapMatrixView(APIView):
    """Capability C: Evidence-Based Skill Gap Analysis."""

    permission_classes = [IsAuthenticated, CanAccessSkillGapMatrix]

    def get(self, request):
        query_serializer = SkillGapMatrixQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        dataset = get_skill_gap_analysis(
            filters=query_serializer.validated_data,
            user=request.user,
        )
        return Response(dataset, status=status.HTTP_200_OK)


class SkillGapMatrixExportView(APIView):
    """Capability C: Export Skill Gap Matrix as Safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessSkillGapMatrix]

    def get(self, request):
        query_serializer = SkillGapMatrixQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        dataset = get_skill_gap_analysis(
            filters=query_serializer.validated_data,
            user=request.user,
        )
        csv_content = export_skill_gaps_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="skill_gap_matrix.csv"'
        return response


class TrainingPlanListCreateView(APIView):
    """Capability D: Retrieve and Create Strategic Training Plans."""

    permission_classes = [IsAuthenticated, CanManageTrainingPlans]

    def get(self, request):
        dataset = get_training_plans_dataset(
            filters=request.query_params.dict(),
            user=request.user,
        )
        return Response(dataset, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = TrainingPlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            plan = create_training_plan(serializer.validated_data, request.user)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(plan.id),
                "title": plan.title,
                "target_skill": plan.target_skill,
                "status": plan.status,
                "message": "Training plan created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class TrainingPlanDetailView(APIView):
    """Capability D: Retrieve single Training Plan."""

    permission_classes = [IsAuthenticated, CanManageTrainingPlans]

    def get(self, request, plan_id):
        plan = TrainingPlan.objects.filter(id=plan_id).first()
        if not plan:
            raise NotFound("Training plan not found.")
        dataset = get_training_plans_dataset(filters={"id": str(plan.id)}, user=request.user)
        matching = [p for p in dataset.get("training_plans", []) if str(p["id"]) == str(plan.id)]
        if not matching:
            raise NotFound("Training plan not found.")
        return Response(matching[0], status=status.HTTP_200_OK)


class TrainingPlanStatusUpdateView(APIView):
    """Capability D: Transition Training Plan status through approval lifecycle."""

    permission_classes = [IsAuthenticated, CanManageTrainingPlans]

    def post(self, request, plan_id):
        plan = TrainingPlan.objects.filter(id=plan_id).first()
        if not plan:
            raise NotFound("Training plan not found.")

        serializer = TrainingPlanStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            updated_plan = update_training_plan_status(
                plan=plan,
                new_status=data["new_status"],
                user=request.user,
                notes=data.get("notes", ""),
                actual_results=data.get("actual_results", ""),
                cancellation_reason=data.get("cancellation_reason", ""),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(updated_plan.id),
                "status": updated_plan.status,
                "status_display": updated_plan.get_status_display(),
                "message": f"Training plan status updated to {updated_plan.get_status_display()}.",
            },
            status=status.HTTP_200_OK,
        )


class TrainingPlanExportView(APIView):
    """Capability D: Export Training Plans as Safe CSV."""

    permission_classes = [IsAuthenticated, CanManageTrainingPlans]

    def get(self, request):
        dataset = get_training_plans_dataset(filters=request.query_params.dict(), user=request.user)
        csv_content = export_training_plans_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="training_plans.csv"'
        return response


class RecruitmentCycleReviewListCreateView(APIView):
    """Capability E: Retrieve and Create Recruitment Cycle Reviews."""

    permission_classes = [IsAuthenticated, CanManageCycleReviews]

    def get(self, request):
        dataset = get_recruitment_cycle_reviews_dataset(
            filters=request.query_params.dict(),
            user=request.user,
        )
        return Response(dataset, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = RecruitmentCycleReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            review = create_recruitment_cycle_review(serializer.validated_data, request.user)
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(review.id),
                "title": review.title,
                "cohort_year": review.cohort_year,
                "status": review.status,
                "message": "Recruitment cycle review initiated with baseline metrics snapshot.",
            },
            status=status.HTTP_201_CREATED,
        )


class RecruitmentCycleReviewDetailView(APIView):
    """Capability E: Retrieve single Recruitment Cycle Review."""

    permission_classes = [IsAuthenticated, CanManageCycleReviews]

    def get(self, request, review_id):
        review = RecruitmentCycleReview.objects.filter(id=review_id).first()
        if not review:
            raise NotFound("Recruitment cycle review not found.")
        dataset = get_recruitment_cycle_reviews_dataset(filters={"cohort_year": review.cohort_year}, user=request.user)
        matching = [r for r in dataset.get("cycle_reviews", []) if str(r["id"]) == str(review.id)]
        if not matching:
            raise NotFound("Recruitment cycle review not found.")
        return Response(matching[0], status=status.HTTP_200_OK)


class RecruitmentCycleStatusUpdateView(APIView):
    """Capability E: Update recruitment cycle review status."""

    permission_classes = [IsAuthenticated, CanManageCycleReviews]

    def post(self, request, review_id):
        review = RecruitmentCycleReview.objects.filter(id=review_id).first()
        if not review:
            raise NotFound("Recruitment cycle review not found.")

        serializer = RecruitmentCycleStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_review = update_recruitment_cycle_status(
                review=review,
                new_status=serializer.validated_data["new_status"],
                user=request.user,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(updated_review.id),
                "status": updated_review.status,
                "status_display": updated_review.get_status_display(),
                "message": f"Recruitment cycle review status updated to {updated_review.get_status_display()}.",
            },
            status=status.HTTP_200_OK,
        )


class CycleImprovementActionCreateView(APIView):
    """Capability E: Create improvement action linked to cycle review."""

    permission_classes = [IsAuthenticated, CanManageCycleReviews]

    def post(self, request, review_id=None):
        target_review_id = review_id or request.data.get("cycle_review_id")
        if not target_review_id:
            raise DRFValidationError(detail="Cycle review ID is required.")
        review = RecruitmentCycleReview.objects.filter(id=target_review_id).first()
        if not review:
            raise NotFound("Recruitment cycle review not found.")

        serializer = CycleImprovementActionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            action = create_cycle_improvement_action(
                review=review,
                data=serializer.validated_data,
                user=request.user,
            )
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(action.id),
                "action_title": action.action_title,
                "status": action.status,
                "category": action.category,
                "message": "Cycle improvement action created successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class CycleImprovementActionStatusUpdateView(APIView):
    """Capability E: Update action status and record resolution notes."""

    permission_classes = [IsAuthenticated, CanManageCycleReviews]

    def post(self, request, action_id):
        action = CycleImprovementAction.objects.filter(id=action_id).first()
        if not action:
            raise NotFound("Cycle improvement action not found.")

        serializer = CycleImprovementActionStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            updated_action = update_cycle_improvement_action_status(
                action=action,
                new_status=data["new_status"],
                user=request.user,
                resolution_notes=data.get("resolution_notes", ""),
            )
        except DjangoValidationError as e:
            raise DRFValidationError(detail=e.message if hasattr(e, "message") else str(e))
        except DjangoPermissionDenied as e:
            raise DRFPermissionDenied(detail=str(e))

        return Response(
            {
                "id": str(updated_action.id),
                "status": updated_action.status,
                "status_display": updated_action.get_status_display(),
                "resolution_notes": updated_action.resolution_notes,
                "message": f"Action status updated to {updated_action.get_status_display()}.",
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request, action_id):
        return self.post(request, action_id)


class ContinuousImprovementDiagnosticsView(APIView):
    """Phase 13: 6-Point Data Quality & Improvement Diagnostics."""

    permission_classes = [IsAuthenticated, CanAccessPlacementRateAnalytics]

    def get(self, request):
        dataset = get_continuous_improvement_diagnostics()
        return Response(dataset, status=status.HTTP_200_OK)
