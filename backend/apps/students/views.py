"""REST API Views for Student Registration, Resumes, Eligibility, and Cohorts."""
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.accounts.models import RoleCatalog
from apps.students.models import (
    JobPublication,
    StudentProfile,
    StudentResume,
    StudentApplication,
    EligibilityEvaluation,
    CandidateCohort,
)
from apps.students.permissions import (
    CanPublishJobNotification,
    CanOverrideEligibility,
    CanFinalizeCohort,
    CanViewCohort,
    IsStudentOwnerOrStaff,
    STAFF_ROLES,
    AUDIT_ROLES,
)
from apps.students.selectors import (
    get_student_profile_by_user,
    get_student_profile_by_id,
    list_student_profiles,
    get_resume_by_id,
    list_resumes_for_student,
    list_publications_for_job,
    get_publication_by_id,
    list_applications_for_job,
    get_cohort_for_job,
    list_cohort_members,
)
from apps.students.services import (
    publish_job_notification,
    retry_job_publication,
    register_student,
    upload_student_resume,
    update_student_profile,
    apply_student_for_job,
    override_candidate_eligibility,
    finalize_candidate_cohort,
)
from apps.students.serializers import (
    JobPublicationSerializer,
    JobPublicationCreateSerializer,
    StudentRegistrationSerializer,
    StudentProfileSerializer,
    StudentProfileUpdateSerializer,
    StudentResumeSerializer,
    StudentResumeUploadSerializer,
    StudentApplicationSerializer,
    EligibilityEvaluationSerializer,
    EligibilityOverrideSerializer,
    CandidateCohortSerializer,
    CohortMemberSerializer,
    CohortFinalizeSerializer,
)


class JobPublicationListCreateAPIView(APIView):
    """List and create job broadcast publications (Workflow Step 10)."""

    def get_permissions(self):
        if self.request.method == "POST":
            return [CanPublishJobNotification()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        job_id = request.query_params.get("job_id")
        if job_id:
            pubs = list_publications_for_job(job_id)
        else:
            # Placement staff see all recent publications
            pubs = JobPublication.objects.select_related(
                "job_requirement", "creative_version", "published_by"
            ).order_by("-created_at")[:50]

        serializer = JobPublicationSerializer(pubs, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = JobPublicationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            pub = publish_job_notification(
                job_requirement_id=str(data["job_requirement_id"]),
                channel=data["channel"],
                target_audience=data["target_audience"],
                creative_version_id=str(data["creative_version_id"]) if data.get("creative_version_id") else None,
                subject=data.get("subject"),
                message_body=data.get("message_body"),
                published_by=request.user,
                request=request,
            )
            return Response(JobPublicationSerializer(pub).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class JobPublicationRetryAPIView(APIView):
    """Retry a failed or pending publication dispatch."""

    permission_classes = [CanPublishJobNotification]

    def post(self, request, pub_id):
        try:
            pub = retry_job_publication(pub_id, user=request.user, request=request)
            return Response(JobPublicationSerializer(pub).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentRegistrationAPIView(APIView):
    """Onboard student account and profile with roll number & email uniqueness (Workflow Step 11)."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user, profile = register_student(
                email=data["email"],
                password=data["password"],
                roll_number=data["roll_number"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                college_name=data["college_name"],
                degree=data["degree"],
                department=data["department"],
                graduation_year=data["graduation_year"],
                cgpa=data["cgpa"],
                active_backlogs=data.get("active_backlogs", 0),
                history_backlogs=data.get("history_backlogs", 0),
                phone_number=data.get("phone_number", ""),
                alternate_phone=data.get("alternate_phone", ""),
                request=request,
            )
            return Response(
                {
                    "message": "Student registration successful. Account created with STUDENT role.",
                    "profile": StudentProfileSerializer(profile).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                return Response(exc.message_dict, status=status.HTTP_400_BAD_REQUEST)
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileMeAPIView(APIView):
    """Retrieve and update current authenticated student's profile."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = get_student_profile_by_user(request.user)
        if not profile:
            return Response(
                {"detail": "No student profile linked to your user account."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(StudentProfileSerializer(profile).data)

    def patch(self, request):
        profile = get_student_profile_by_user(request.user)
        if not profile:
            return Response(
                {"detail": "No student profile linked to your user account."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = StudentProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = update_student_profile(profile, serializer.validated_data, user=request.user, request=request)
            return Response(StudentProfileSerializer(updated).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileDetailAPIView(APIView):
    """Retrieve or update specific student profile by ID with object-level isolation."""

    permission_classes = [IsStudentOwnerOrStaff]

    def get(self, request, profile_id):
        profile = get_student_profile_by_id(profile_id)
        if not profile:
            raise Http404("Student profile not found.")
        self.check_object_permissions(request, profile)
        return Response(StudentProfileSerializer(profile).data)

    def patch(self, request, profile_id):
        profile = get_student_profile_by_id(profile_id)
        if not profile:
            raise Http404("Student profile not found.")
        self.check_object_permissions(request, profile)

        serializer = StudentProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated = update_student_profile(profile, serializer.validated_data, user=request.user, request=request)
            return Response(StudentProfileSerializer(updated).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentProfileListAPIView(APIView):
    """List all student profiles with filtering for placement staff."""

    permission_classes = [CanViewCohort]

    def get(self, request):
        search = request.query_params.get("search")
        department = request.query_params.get("department")
        grad_year = request.query_params.get("graduation_year")
        min_cgpa = request.query_params.get("min_cgpa")
        is_verified = request.query_params.get("is_verified")

        profiles = list_student_profiles(
            search=search,
            department=department,
            graduation_year=int(grad_year) if grad_year else None,
            min_cgpa=float(min_cgpa) if min_cgpa else None,
            is_verified=is_verified.lower() == "true" if is_verified else None,
        )
        return Response(StudentProfileSerializer(profiles, many=True).data)


class StudentResumeUploadAPIView(APIView):
    """Upload resume PDF with %PDF- signature and 5MB boundary checks (Workflow Step 12)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = get_student_profile_by_user(request.user)
        if not profile:
            return Response(
                {"detail": "Only accounts with a student profile may upload resumes."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = StudentResumeUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data["file"]

        try:
            resume = upload_student_resume(profile, file_obj, user=request.user, request=request)
            return Response(StudentResumeSerializer(resume).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentResumeDownloadAPIView(APIView):
    """Private, authenticated resume streaming download endpoint with strict object-level isolation."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, resume_id):
        resume = get_resume_by_id(resume_id)
        if not resume:
            raise Http404("Resume document not found.")

        # Check access permission: student owner OR authorized staff/auditor
        user_roles = request.user.get_active_roles()
        is_staff = any(r in AUDIT_ROLES for r in user_roles) or request.user.is_superuser
        if not is_staff and resume.student.user != request.user:
            return Response(
                {"detail": "Access denied. You cannot view another student's resume document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = FileResponse(resume.file.open("rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{resume.file_name or "resume.pdf"}"'
        return response


class StudentApplicationApplyAPIView(APIView):
    """Student submits drive application and triggers deterministic eligibility engine (Workflow Step 13)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        profile = get_student_profile_by_user(request.user)
        if not profile:
            return Response(
                {"detail": "Only registered students can apply for placement opportunities."},
                status=status.HTTP_403_FORBIDDEN,
            )

        job_id = request.data.get("job_requirement_id")
        if not job_id:
            return Response(
                {"job_requirement_id": "This field is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            app = apply_student_for_job(profile, job_id, user=request.user, request=request)
            return Response(StudentApplicationSerializer(app).data, status=status.HTTP_201_CREATED)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentApplicationListAPIView(APIView):
    """List applications for a job or for the currently logged-in student."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        job_id = request.query_params.get("job_id")
        user_roles = request.user.get_active_roles()
        is_staff = any(r in AUDIT_ROLES for r in user_roles) or request.user.is_superuser

        if not is_staff:
            # Student view: only return their own applications
            profile = get_student_profile_by_user(request.user)
            if not profile:
                return Response([])
            apps = StudentApplication.objects.filter(student=profile).select_related(
                "job_requirement", "job_requirement__company", "resume", "eligibility_evaluation"
            )
            if job_id:
                apps = apps.filter(job_requirement_id=job_id)
            return Response(StudentApplicationSerializer(apps, many=True).data)

        # Staff view
        if not job_id:
            return Response(
                {"detail": "Parameter 'job_id' is required for placement staff directory queries."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        status_filter = request.query_params.get("status")
        apps = list_applications_for_job(job_id, status=status_filter)
        return Response(StudentApplicationSerializer(apps, many=True).data)


class EligibilityEvaluationDetailAPIView(APIView):
    """Retrieve criterion-by-criterion eligibility evaluation breakdown."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, eval_id):
        try:
            evaluation = EligibilityEvaluation.objects.select_related(
                "application", "application__student", "application__job_requirement"
            ).get(id=eval_id)
        except EligibilityEvaluation.DoesNotExist:
            raise Http404("Eligibility evaluation not found.")

        # Access check
        user_roles = request.user.get_active_roles()
        is_staff = any(r in AUDIT_ROLES for r in user_roles) or request.user.is_superuser
        if not is_staff and evaluation.application.student.user != request.user:
            return Response(
                {"detail": "Access denied. Cannot view another student's eligibility records."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return Response(EligibilityEvaluationSerializer(evaluation).data)


class EligibilityOverrideAPIView(APIView):
    """Authorize a manual eligibility override with mandatory reason (Workflow Step 14)."""

    permission_classes = [CanOverrideEligibility]

    def post(self, request, eval_id):
        serializer = EligibilityOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            evaluation = override_candidate_eligibility(
                evaluation_id=eval_id,
                new_is_eligible=data["is_eligible"],
                override_reason=data["override_reason"],
                override_by=request.user,
                request=request,
            )
            return Response(EligibilityEvaluationSerializer(evaluation).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class CandidateCohortDetailAPIView(APIView):
    """Retrieve the candidate cohort and members for an approved job requirement."""

    permission_classes = [CanViewCohort]

    def get(self, request, job_id):
        cohort = get_cohort_for_job(job_id)
        if not cohort:
            return Response(
                {"detail": "Candidate cohort has not been compiled yet for this job requirement."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CandidateCohortSerializer(cohort).data)


class CandidateCohortFinalizeAPIView(APIView):
    """Formally lock the candidate cohort (Placement Head or Admin only; Step 14)."""

    permission_classes = [CanFinalizeCohort]

    def post(self, request, job_id):
        serializer = CohortFinalizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notes = serializer.validated_data.get("notes", "")

        try:
            cohort = finalize_candidate_cohort(
                job_requirement_id=job_id,
                finalized_by=request.user,
                notes=notes,
                request=request,
            )
            return Response(CandidateCohortSerializer(cohort).data, status=status.HTTP_200_OK)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
