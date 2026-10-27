"""DRF ViewSets and API Views for Interview Management & Tracking (Phase 8 / Steps 29-35)."""
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from apps.interviews.permissions import (
    CanManageInterviews,
    CanManageInterviewRounds,
    IsStudentOrStaffInterviewAccess,
)
from apps.interviews import selectors, services
from apps.interviews.serializers import (
    CandidateShortlistSerializer,
    CandidateShortlistCreateSerializer,
    InterviewScheduleSerializer,
    InterviewScheduleCreateSerializer,
    InterviewRescheduleSerializer,
    AttendanceConfirmationSerializer,
    InterviewConductedSerializer,
    InterviewNotificationLogSerializer,
    InterviewRoundSerializer,
    InterviewRoundCreateSerializer,
    InterviewRoundEvaluateSerializer,
    HRInterviewFollowUpSerializer,
    HRInterviewFollowUpCreateSerializer,
)


class CandidateShortlistViewSet(viewsets.ViewSet):
    """API endpoints for HR Candidate Shortlist intake (Step 29)."""

    permission_classes = [permissions.IsAuthenticated, CanManageInterviews]

    def list(self, request):
        job_id = request.query_params.get("job_id")
        company_id = request.query_params.get("company_id")
        search = request.query_params.get("search")
        shortlists = selectors.get_shortlists(
            job_id=job_id,
            company_id=company_id,
            search=search,
        )
        serializer = CandidateShortlistSerializer(shortlists, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = CandidateShortlistCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            shortlist = services.receive_candidate_shortlist(
                job_id=str(vd["job_id"]),
                company_id=str(vd["company_id"]),
                hr_contact_id=str(vd["hr_contact_id"]),
                student_ids=[str(sid) for sid in vd["student_ids"]],
                created_by=request.user,
                submission_package_id=str(vd["submission_package_id"]) if vd.get("submission_package_id") else None,
                source=vd.get("source", "EMAIL"),
                received_at=vd.get("received_at"),
                notes=vd.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = CandidateShortlistSerializer(shortlist)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        shortlist = selectors.get_shortlist_by_id(pk)
        if not shortlist:
            return Response({"detail": "Shortlist not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = CandidateShortlistSerializer(shortlist)
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], url_path="submittable-candidates")
    def submittable_candidates(self, request):
        job_id = request.query_params.get("job_id")
        if not job_id:
            return Response({"detail": "job_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        data = selectors.get_eligible_submissions_for_shortlist(job_id)
        return Response(data)


class InterviewScheduleViewSet(viewsets.ViewSet):
    """API endpoints for Interview Schedules (Steps 30, 31, 32, 33)."""

    def get_permissions(self):
        if self.action in ["confirm_attendance"]:
            return [permissions.IsAuthenticated(), IsStudentOrStaffInterviewAccess()]
        return [permissions.IsAuthenticated(), CanManageInterviews()]

    def list(self, request):
        schedules = selectors.get_interview_schedules(
            job_id=request.query_params.get("job_id"),
            company_id=request.query_params.get("company_id"),
            student_id=request.query_params.get("student_id"),
            status=request.query_params.get("status"),
            attendance_status=request.query_params.get("attendance_status"),
            conducted_status=request.query_params.get("conducted_status"),
            search=request.query_params.get("search"),
        )
        serializer = InterviewScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = InterviewScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            schedule = services.create_interview_schedule(
                candidate_id=str(vd["candidate_id"]),
                interview_date=vd["interview_date"],
                interview_time=vd["interview_time"],
                created_by=request.user,
                mode=vd.get("mode", "ONLINE"),
                venue=vd.get("venue", ""),
                meeting_link=vd.get("meeting_link", ""),
                required_documents=vd.get("required_documents", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewScheduleSerializer(schedule)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        schedule = selectors.get_interview_schedule_by_id(pk)
        if not schedule:
            return Response({"detail": "Interview schedule not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = InterviewScheduleSerializer(schedule)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"], url_path="reschedule")
    def reschedule(self, request, pk=None):
        serializer = InterviewRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            new_schedule = services.reschedule_interview(
                schedule_id=pk,
                new_date=vd["new_date"],
                new_time=vd["new_time"],
                user=request.user,
                new_mode=vd.get("new_mode"),
                new_venue=vd.get("new_venue"),
                new_meeting_link=vd.get("new_meeting_link"),
                new_required_documents=vd.get("new_required_documents"),
                reschedule_reason=vd.get("reschedule_reason", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewScheduleSerializer(new_schedule)
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], url_path="notify")
    def notify(self, request, pk=None):
        channel = request.data.get("channel", "EMAIL")
        try:
            log = services.notify_student_of_interview(
                schedule_id=pk,
                user=request.user,
                channel=channel,
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewNotificationLogSerializer(log)
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], url_path="confirm-attendance")
    def confirm_attendance(self, request, pk=None):
        serializer = AttendanceConfirmationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        is_student = "STUDENT" in user_roles and not (request.user.is_staff or request.user.is_superuser)

        try:
            schedule = services.record_attendance_confirmation(
                schedule_id=pk,
                attendance_status=vd["attendance_status"],
                user=request.user,
                notes=vd.get("notes", ""),
                is_student_self_confirm=is_student,
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewScheduleSerializer(schedule)
        return Response(out_serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["POST"], url_path="record-conducted")
    def record_conducted(self, request, pk=None):
        serializer = InterviewConductedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            schedule = services.record_interview_conducted(
                schedule_id=pk,
                conducted_status=vd["conducted_status"],
                user=request.user,
                notes=vd.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewScheduleSerializer(schedule)
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class ProcessDueRemindersView(APIView):
    """Trigger dispatch of scheduled automatic reminders (Step 31)."""

    permission_classes = [permissions.IsAuthenticated, CanManageInterviews]

    def post(self, request):
        processed_count = services.process_due_reminders(user=request.user)
        return Response({
            "message": f"Successfully processed {processed_count} due automatic reminders.",
            "processed_count": processed_count,
        }, status=status.HTTP_200_OK)


class InterviewRoundViewSet(viewsets.ViewSet):
    """API endpoints for categorized interview rounds (Step 34)."""

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.IsAuthenticated(), IsStudentOrStaffInterviewAccess()]
        return [permissions.IsAuthenticated(), CanManageInterviewRounds()]

    def list(self, request):
        candidate_id = request.query_params.get("candidate_id")
        job_id = request.query_params.get("job_id")
        category = request.query_params.get("category")
        round_status = request.query_params.get("status")

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if "STUDENT" in user_roles and not (request.user.is_staff or request.user.is_superuser):
            student_profile = getattr(request.user, "student_profile", None)
            if not student_profile:
                return Response([])
            candidate_id = student_profile.shortlisted_interviews.values_list("id", flat=True)

        rounds = selectors.get_interview_rounds(
            candidate_id=candidate_id if isinstance(candidate_id, str) else None,
            job_id=job_id,
            category=category,
            status=round_status,
        )
        serializer = InterviewRoundSerializer(rounds, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        serializer = InterviewRoundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            round_obj = services.create_interview_round(
                candidate_id=str(vd["candidate_id"]),
                category=vd["category"],
                user=request.user,
                round_name=vd.get("round_name", ""),
                scheduled_date=vd.get("scheduled_date"),
                scheduled_time=vd.get("scheduled_time"),
                interviewer_names=vd.get("interviewer_names", ""),
                internal_staff_notes=vd.get("internal_staff_notes", ""),
                schedule_id=str(vd["schedule_id"]) if vd.get("schedule_id") else None,
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewRoundSerializer(round_obj, context={"request": request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"], url_path="evaluate")
    def evaluate(self, request, pk=None):
        serializer = InterviewRoundEvaluateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            round_obj = services.evaluate_interview_round(
                round_id=pk,
                status=vd["status"],
                user=request.user,
                internal_staff_notes=vd.get("internal_staff_notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = InterviewRoundSerializer(round_obj, context={"request": request})
        return Response(out_serializer.data, status=status.HTTP_200_OK)


class HRInterviewFollowUpViewSet(viewsets.ViewSet):
    """API endpoints for HR follow-up tracking (Step 35)."""

    permission_classes = [permissions.IsAuthenticated, CanManageInterviews]

    def list(self, request):
        job_id = request.query_params.get("job_id")
        company_id = request.query_params.get("company_id")
        overdue_only = request.query_params.get("overdue_only", "").lower() in ("true", "1")
        search = request.query_params.get("search")

        follow_ups = selectors.get_hr_follow_ups(
            job_id=job_id,
            company_id=company_id,
            overdue_only=overdue_only,
            search=search,
        )
        serializer = HRInterviewFollowUpSerializer(follow_ups, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = HRInterviewFollowUpCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            follow_up = services.record_hr_follow_up(
                job_id=str(vd["job_id"]),
                company_id=str(vd["company_id"]),
                hr_contact_id=str(vd["hr_contact_id"]),
                candidate_status_reported=vd["candidate_status_reported"],
                user=request.user,
                pending_rounds=vd.get("pending_rounds", ""),
                expected_result_date=vd.get("expected_result_date"),
                is_date_confirmed=vd.get("is_date_confirmed", True),
                next_follow_up_date=vd.get("next_follow_up_date"),
                channel=vd.get("channel", "PHONE_CALL"),
                response_status=vd.get("response_status", "RESPONSE_RECEIVED"),
                hr_response_summary=vd.get("hr_response_summary", ""),
                notes=vd.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e.message if hasattr(e, "message") else e)}, status=status.HTTP_400_BAD_REQUEST)

        out_serializer = HRInterviewFollowUpSerializer(follow_up)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class StudentMyInterviewsView(APIView):
    """Student-isolated view of personal interview schedules."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            return Response({"detail": "User is not a registered student candidate."}, status=status.HTTP_403_FORBIDDEN)

        schedules = selectors.get_student_interview_schedules(student_profile)
        serializer = InterviewScheduleSerializer(schedules, many=True)
        return Response(serializer.data)


class InterviewKPIView(APIView):
    """Aggregate metrics for the Interview Management workspace."""

    permission_classes = [permissions.IsAuthenticated, CanManageInterviews]

    def get(self, request):
        kpis = selectors.get_interview_kpis()
        return Response(kpis)
