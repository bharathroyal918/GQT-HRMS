"""Views and ViewSets for Phase 9 Feedback Collection."""
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.feedback import selectors, services
from apps.feedback.permissions import (
    CanManageHRFeedback,
    CanManageTrainerFeedback,
    CanViewFeedbackSummary,
    IsStudentOrStaffForStudentFeedback,
)
from apps.feedback.serializers import (
    FeedbackKPISerializer,
    HRFeedbackCreateSerializer,
    HRFeedbackSerializer,
    HRFeedbackUpdateSerializer,
    StudentFeedbackCreateSerializer,
    StudentFeedbackSerializer,
    StudentFeedbackUpdateSerializer,
    TrainerFeedbackCreateSerializer,
    TrainerFeedbackSerializer,
    TrainerFeedbackUpdateSerializer,
)


class StudentFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student interview experience feedback (Step 9 Category A)."""

    serializer_class = StudentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsStudentOrStaffForStudentFeedback]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return selectors.get_student_feedback_queryset(self.request.user, self.request.query_params)

    def create(self, request, *args, **kwargs):
        input_serializer = StudentFeedbackCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        feedback = services.submit_student_feedback(request.user, input_serializer.validated_data)
        output_serializer = self.get_serializer(feedback)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        input_serializer = StudentFeedbackUpdateSerializer(data=request.data, partial=True)
        input_serializer.is_valid(raise_exception=True)
        updated = services.update_student_feedback(request.user, str(instance.id), input_serializer.validated_data)
        output_serializer = self.get_serializer(updated)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class HRFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for corporate HR recruiter feedback on candidate caliber and satisfaction (Step 9 Category B)."""

    serializer_class = HRFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageHRFeedback]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return selectors.get_hr_feedback_queryset(self.request.user, self.request.query_params)

    def create(self, request, *args, **kwargs):
        input_serializer = HRFeedbackCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        feedback = services.submit_hr_feedback(request.user, input_serializer.validated_data)
        output_serializer = self.get_serializer(feedback)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        input_serializer = HRFeedbackUpdateSerializer(data=request.data, partial=True)
        input_serializer.is_valid(raise_exception=True)
        updated = services.update_hr_feedback(request.user, str(instance.id), input_serializer.validated_data)
        output_serializer = self.get_serializer(updated)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class TrainerFeedbackViewSet(viewsets.ModelViewSet):
    """ViewSet for placement trainer evaluation of candidate readiness and improvement areas (Step 9 Category C)."""

    serializer_class = TrainerFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageTrainerFeedback]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return selectors.get_trainer_feedback_queryset(self.request.user, self.request.query_params)

    def create(self, request, *args, **kwargs):
        input_serializer = TrainerFeedbackCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        feedback = services.submit_trainer_feedback(request.user, input_serializer.validated_data)
        output_serializer = self.get_serializer(feedback)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        input_serializer = TrainerFeedbackUpdateSerializer(data=request.data, partial=True)
        input_serializer.is_valid(raise_exception=True)
        updated = services.update_trainer_feedback(request.user, str(instance.id), input_serializer.validated_data)
        output_serializer = self.get_serializer(updated)
        return Response(output_serializer.data, status=status.HTTP_200_OK)


class FeedbackSummaryAPIView(APIView):
    """Retrieve aggregated KPI counts and rating averages across feedback categories."""

    permission_classes = [permissions.IsAuthenticated, CanViewFeedbackSummary]

    def get(self, request, *args, **kwargs):
        kpis = selectors.get_feedback_kpis(request.user)
        serializer = FeedbackKPISerializer(kpis)
        return Response(serializer.data, status=status.HTTP_200_OK)


class StudentEligibleDrivesAPIView(APIView):
    """List distinct participating interview drives for the authenticated student candidate."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        schedules = selectors.get_student_eligible_interview_drives(request.user)
        data = [
            {
                "interview_schedule_id": str(s.id),
                "company_id": str(s.job_requirement.company.id) if s.job_requirement else None,
                "company_name": s.job_requirement.company.name if s.job_requirement else "General Drive",
                "job_requirement_id": str(s.job_requirement.id) if s.job_requirement else None,
                "job_title": s.job_requirement.title if s.job_requirement else "Recruitment Drive",
                "interview_date": s.interview_date.isoformat(),
            }
            for s in schedules
        ]
        return Response(data, status=status.HTTP_200_OK)
