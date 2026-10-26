"""API Views for Student Preparation Workflow (Phase 6 / Steps 15-23)."""
from django.core.exceptions import ValidationError, PermissionDenied
from rest_framework import generics, status, views
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import RoleCatalog
from apps.preparation.models import (
    ResumeReview,
    ResumeImprovementCycle,
    AssessmentTest,
    StudentAssessmentAttempt,
    TrainingSession,
    TrainingAttendance,
    MockInterview,
    PlacementReadinessCertification,
)
from apps.preparation.permissions import (
    IsTrainerOrStaff,
    IsEvaluatorOrStaff,
    CanCertifyPlacementReadiness,
    IsStudentOrStaff,
    EVALUATOR_ROLES,
)
from apps.preparation.selectors import (
    get_resume_reviews,
    get_active_assessment_tests,
    get_student_attempts,
    get_training_sessions,
    get_mock_interviews,
    get_placement_certifications,
    get_student_readiness_snapshot,
)
from apps.preparation.serializers import (
    ResumeReviewSerializer,
    ResumeReviewCreateSerializer,
    ResumeImprovementCycleSerializer,
    AssessmentTestListSerializer,
    AssessmentTestDetailSerializer,
    StudentAssessmentAttemptSerializer,
    StartAssessmentAttemptSerializer,
    SubmitAssessmentAttemptSerializer,
    TrainingSessionSerializer,
    TrainingAttendanceSerializer,
    RecordAttendanceSerializer,
    MockInterviewSerializer,
    ScheduleMockInterviewSerializer,
    SubmitMockEvaluationSerializer,
    MockInterviewEvaluationSerializer,
    PlacementReadinessCertificationSerializer,
    CertifyPlacementReadinessRequestSerializer,
)
from apps.preparation.services import (
    review_resume_rubric,
    submit_improved_resume,
    start_assessment_attempt,
    submit_assessment_attempt,
    record_training_attendance,
    schedule_mock_interview,
    evaluate_mock_interview,
    certify_placement_readiness,
)
from apps.students.models import StudentProfile


# ==============================================================================
# Step 15: Resume Review Views
# ==============================================================================

class ResumeReviewListCreateView(views.APIView):
    """List resume reviews (scoped to student for candidates) or create review (Trainers/Staff)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        student_id = request.query_params.get("student_id")
        resume_id = request.query_params.get("resume_id")
        status_filter = request.query_params.get("status")

        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            # Strict candidate isolation
            if hasattr(request.user, "student_profile"):
                student_id = str(request.user.student_profile.id)
            else:
                return Response([])

        reviews = get_resume_reviews(
            student_id=student_id,
            resume_id=resume_id,
            status=status_filter,
        )
        serializer = ResumeReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Only Trainers or Staff can submit reviews
        perm = IsTrainerOrStaff()
        if not perm.has_permission(request, self):
            return Response(
                {"detail": "Only Placement Trainers and Staff can submit resume reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = ResumeReviewCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            review = review_resume_rubric(
                resume_id=str(serializer.validated_data["resume_id"]),
                reviewer=request.user,
                status=serializer.validated_data["status"],
                formatting_score=serializer.validated_data["formatting_score"],
                technical_skills_score=serializer.validated_data["technical_skills_score"],
                projects_score=serializer.validated_data["projects_score"],
                achievements_score=serializer.validated_data["achievements_score"],
                detailed_feedback=serializer.validated_data["detailed_feedback"],
                suggested_improvements=serializer.validated_data.get("suggested_improvements", ""),
                request=request,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ResumeReviewSerializer(review).data, status=status.HTTP_201_CREATED)


# ==============================================================================
# Step 16: Resume Improvement Views
# ==============================================================================

class ResumeImprovementCycleListView(views.APIView):
    """List resume improvement cycles."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        qs = ResumeImprovementCycle.objects.select_related(
            "student__user", "initial_review", "prior_resume", "improved_resume"
        ).all()

        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, "student_profile"):
                qs = qs.filter(student=request.user.student_profile)
            else:
                return Response([])
        else:
            student_id = request.query_params.get("student_id")
            if student_id:
                qs = qs.filter(student_id=student_id)

        serializer = ResumeImprovementCycleSerializer(qs, many=True)
        return Response(serializer.data)


class ResumeImprovementSubmitView(views.APIView):
    """Student re-uploads improved resume PDF with monotonic versioning (Step 16)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "User account does not have an associated student profile."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_obj = request.FILES.get("file")
        if not file_obj:
            return Response({"detail": "Resume file is required."}, status=status.HTTP_400_BAD_REQUEST)

        student_notes = request.data.get("student_notes", "")

        try:
            resume, cycle = submit_improved_resume(
                student_profile=request.user.student_profile,
                file_obj=file_obj,
                student_notes=student_notes,
                user=request.user,
                request=request,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "message": f"Resume v{resume.version_number} uploaded successfully.",
                "resume_id": str(resume.id),
                "version_number": resume.version_number,
                "cycle_id": str(cycle.id) if cycle else None,
            },
            status=status.HTTP_201_CREATED,
        )


# ==============================================================================
# Steps 17 & 18: Assessment Test & Attempt Views
# ==============================================================================

class AssessmentTestListView(views.APIView):
    """List available active assessment tests."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        test_type = request.query_params.get("test_type")
        tests = get_active_assessment_tests(test_type=test_type)
        serializer = AssessmentTestListSerializer(tests, many=True)
        return Response(serializer.data)


class AssessmentTestDetailView(views.APIView):
    """Retrieve test details with sanitized questions for students (answer keys strictly stripped)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            test = AssessmentTest.objects.select_related("created_by").get(id=pk)
        except AssessmentTest.DoesNotExist:
            return Response({"detail": "Assessment test not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AssessmentTestDetailSerializer(test, context={"request": request})
        return Response(serializer.data)


class AssessmentAttemptStartView(views.APIView):
    """Student starts an assessment attempt (timed session)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hasattr(request.user, "student_profile"):
            return Response(
                {"detail": "Only registered candidates can take assessments."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StartAssessmentAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attempt = start_assessment_attempt(
                student_profile=request.user.student_profile,
                test_id=str(serializer.validated_data["test_id"]),
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StudentAssessmentAttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class AssessmentAttemptSubmitView(views.APIView):
    """Submit student answers and execute deterministic server-side grading."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SubmitAssessmentAttemptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attempt = submit_assessment_attempt(
                attempt_id=str(serializer.validated_data["attempt_id"]),
                answers=serializer.validated_data["answers"],
                user=request.user,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(StudentAssessmentAttemptSerializer(attempt).data, status=status.HTTP_200_OK)


class AssessmentAttemptListView(views.APIView):
    """List student attempts (students see their own; staff can inspect all)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        student_id = request.query_params.get("student_id")
        test_id = request.query_params.get("test_id")

        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, "student_profile"):
                student_id = str(request.user.student_profile.id)
            else:
                return Response([])

        attempts = get_student_attempts(student_id=student_id, test_id=test_id)
        serializer = StudentAssessmentAttemptSerializer(attempts, many=True)
        return Response(serializer.data)


# ==============================================================================
# Steps 19 & 20: Communication & Grooming Session Views
# ==============================================================================

class TrainingSessionListView(views.APIView):
    """List or create training & grooming workshops."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_type = request.query_params.get("session_type")
        sessions = get_training_sessions(session_type=session_type)
        serializer = TrainingSessionSerializer(sessions, many=True)
        return Response(serializer.data)

    def post(self, request):
        perm = IsTrainerOrStaff()
        if not perm.has_permission(request, self):
            return Response({"detail": "Only trainers and staff can schedule workshops."}, status=status.HTTP_403_FORBIDDEN)

        serializer = TrainingSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = serializer.save(trainer=request.user)
        return Response(TrainingSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class TrainingAttendanceListView(views.APIView):
    """List training attendance records."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        session_id = request.query_params.get("session_id")
        student_id = request.query_params.get("student_id")
        qs = TrainingAttendance.objects.select_related("session", "student__user").all()

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, "student_profile"):
                qs = qs.filter(student=request.user.student_profile)
            else:
                return Response([])
        else:
            if student_id:
                qs = qs.filter(student_id=student_id)

        if session_id:
            qs = qs.filter(session_id=session_id)

        serializer = TrainingAttendanceSerializer(qs, many=True)
        return Response(serializer.data)


class RecordTrainingAttendanceView(views.APIView):
    """Trainer records attendance, presentation scores, and grooming criteria (Steps 19 & 20)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        perm = IsTrainerOrStaff()
        if not perm.has_permission(request, self):
            return Response({"detail": "Only trainers and staff can record attendance."}, status=status.HTTP_403_FORBIDDEN)

        serializer = RecordAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            attendance = record_training_attendance(
                session_id=str(serializer.validated_data["session_id"]),
                student_id=str(serializer.validated_data["student_id"]),
                attendance_status=serializer.validated_data["attendance_status"],
                presentation_score=serializer.validated_data.get("presentation_score"),
                professional_etiquette_verified=serializer.validated_data.get("professional_etiquette_verified", False),
                corporate_communication_verified=serializer.validated_data.get("corporate_communication_verified", False),
                dress_code_verified=serializer.validated_data.get("dress_code_verified", False),
                hr_interview_ready=serializer.validated_data.get("hr_interview_ready", False),
                grooming_certified=serializer.validated_data.get("grooming_certified", False),
                trainer_remarks=serializer.validated_data.get("trainer_remarks", ""),
                trainer=request.user,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(TrainingAttendanceSerializer(attendance).data, status=status.HTTP_200_OK)


# ==============================================================================
# Steps 21 & 22: Mock Interview & Rubric Evaluation Views
# ==============================================================================

class MockInterviewListCreateView(views.APIView):
    """List mock interviews or schedule a new mock interview (Step 21)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        student_id = request.query_params.get("student_id")
        evaluator_id = request.query_params.get("evaluator_id")
        status_filter = request.query_params.get("status")

        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, "student_profile"):
                student_id = str(request.user.student_profile.id)
            else:
                return Response([])
        elif RoleCatalog.EVALUATOR in user_roles and not (request.user.is_staff or request.user.is_superuser):
            evaluator_id = str(request.user.id)

        mocks = get_mock_interviews(
            student_id=student_id,
            evaluator_id=evaluator_id,
            status=status_filter,
        )
        serializer = MockInterviewSerializer(mocks, many=True)
        return Response(serializer.data)

    def post(self, request):
        perm = IsTrainerOrStaff()
        if not perm.has_permission(request, self):
            return Response({"detail": "Only placement staff and trainers can schedule mock interviews."}, status=status.HTTP_403_FORBIDDEN)

        serializer = ScheduleMockInterviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            mock = schedule_mock_interview(
                student_id=str(serializer.validated_data["student_id"]),
                evaluator_id=str(serializer.validated_data["evaluator_id"]),
                scheduled_by=request.user,
                scheduled_at=serializer.validated_data["scheduled_at"],
                interview_type=serializer.validated_data.get("interview_type", "COMBINED"),
                meeting_link=serializer.validated_data.get("meeting_link", ""),
                notes=serializer.validated_data.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MockInterviewSerializer(mock).data, status=status.HTTP_201_CREATED)


class MockInterviewEvaluateView(views.APIView):
    """Evaluator submits rubric scorecard and candidate readiness recommendation (Step 22)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        perm = IsEvaluatorOrStaff()
        if not perm.has_permission(request, self):
            return Response({"detail": "Only assigned evaluators and staff can evaluate mock interviews."}, status=status.HTTP_403_FORBIDDEN)

        serializer = SubmitMockEvaluationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            evaluation = evaluate_mock_interview(
                mock_interview_id=str(serializer.validated_data["mock_interview_id"]),
                evaluator=request.user,
                technical_competence_score=serializer.validated_data["technical_competence_score"],
                problem_solving_score=serializer.validated_data["problem_solving_score"],
                communication_clarity_score=serializer.validated_data["communication_clarity_score"],
                professional_readiness_score=serializer.validated_data["professional_readiness_score"],
                technical_feedback=serializer.validated_data["technical_feedback"],
                communication_feedback=serializer.validated_data["communication_feedback"],
                improvement_suggestions=serializer.validated_data["improvement_suggestions"],
                readiness_recommendation=serializer.validated_data["readiness_recommendation"],
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MockInterviewEvaluationSerializer(evaluation).data, status=status.HTTP_200_OK)


# ==============================================================================
# Step 23: Final Placement Resume Approval Gate Views
# ==============================================================================

class PlacementReadinessSnapshotView(views.APIView):
    """Retrieve comprehensive readiness checklist criteria for a candidate across Steps 15-22."""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        # Candidate isolation check
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if not hasattr(request.user, "student_profile") or str(request.user.student_profile.id) != str(student_id):
                return Response({"detail": "Access denied to candidate readiness records."}, status=status.HTTP_403_FORBIDDEN)

        try:
            snapshot = get_student_readiness_snapshot(student_id)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Student profile not found."}, status=status.HTTP_404_NOT_FOUND)

        return Response(snapshot)


class PlacementReadinessCertificationListView(views.APIView):
    """List authoritative placement readiness certifications."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        student_id = request.query_params.get("student_id")
        is_approved_str = request.query_params.get("is_approved")
        is_approved = is_approved_str.lower() == "true" if is_approved_str is not None else None

        if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
            if hasattr(request.user, "student_profile"):
                student_id = str(request.user.student_profile.id)
            else:
                return Response([])

        certs = get_placement_certifications(student_id=student_id, is_approved=is_approved)
        serializer = PlacementReadinessCertificationSerializer(certs, many=True)
        return Response(serializer.data)


class CertifyPlacementReadinessView(views.APIView):
    """Placement Head formal certification gate approving resume for placement drives (Step 23 Gate)."""

    permission_classes = [IsAuthenticated, CanCertifyPlacementReadiness]

    def post(self, request):
        serializer = CertifyPlacementReadinessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            cert = certify_placement_readiness(
                student_id=str(serializer.validated_data["student_id"]),
                approved_resume_id=str(serializer.validated_data["approved_resume_id"]),
                certified_by=request.user,
                is_approved=serializer.validated_data.get("is_approved", True),
                notes=serializer.validated_data.get("notes", ""),
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(PlacementReadinessCertificationSerializer(cert).data, status=status.HTTP_200_OK)
