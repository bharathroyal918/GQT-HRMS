"""REST API Views for Candidate Submissions & Profile Dispatch (Phase 7 / Steps 24-28)."""
import logging
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import FileResponse, Http404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.submissions.permissions import (
    CanManageSubmissions,
    CanAcknowledgeSubmissions,
    IsStudentOrStaffSubmissionAccess,
    AUDIT_ROLES,
)
from apps.submissions.selectors import (
    get_eligible_candidates_for_job,
    get_submission_packages,
    get_submission_package_by_id,
    get_student_submissions,
)
from apps.submissions.services import (
    create_submission_package,
    generate_candidate_roster_spreadsheet,
    verify_and_attach_resumes,
    dispatch_candidate_profiles_to_hr,
    record_company_acknowledgement,
)
from apps.submissions.serializers import (
    CandidateEligibilityReadinessSerializer,
    SubmissionPackageListSerializer,
    SubmissionPackageDetailSerializer,
    CreateSubmissionPackageSerializer,
    DispatchPackageSerializer,
    RecordAcknowledgementSerializer,
    StudentSubmissionSerializer,
)

logger = logging.getLogger("apps.submissions")


class JobEligibleCandidatesAPIView(APIView):
    """Retrieve candidate pool for an approved job, showing eligibility and Step 23 readiness certification (Step 24)."""

    permission_classes = [permissions.IsAuthenticated, CanManageSubmissions]

    def get(self, request, job_id):
        data = get_eligible_candidates_for_job(str(job_id))
        if not data.get("job_id"):
            raise Http404("Job requirement not found.")

        candidates_data = CandidateEligibilityReadinessSerializer(data["candidates"], many=True).data
        return Response({
            "job_id": data["job_id"],
            "job_title": data["job_title"],
            "company_name": data["company_name"],
            "hr_contact_name": data["hr_contact_name"],
            "hr_contact_email": data["hr_contact_email"],
            "total_eligible": data["total_eligible"],
            "total_certified": data["total_certified"],
            "candidates": candidates_data,
        })


class SubmissionPackageListCreateAPIView(APIView):
    """List existing submission packages or assemble a new candidate submission package (Step 24)."""

    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [permissions.IsAuthenticated(), CanManageSubmissions()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        # Verify user has access to view submission directory
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if not (user_roles & AUDIT_ROLES or request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Access denied. Placement staff role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        job_id = request.query_params.get("job_id")
        company_id = request.query_params.get("company_id")
        status_param = request.query_params.get("status")

        packages = get_submission_packages(
            job_requirement_id=job_id,
            company_id=company_id,
            status=status_param,
        )
        serializer = SubmissionPackageListSerializer(packages, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CreateSubmissionPackageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            package = create_submission_package(
                job_requirement_id=str(vd["job_requirement_id"]),
                candidate_student_ids=[str(cid) for cid in vd["candidate_student_ids"]],
                user=request.user,
                title=vd.get("title", ""),
                notes=vd.get("notes", ""),
            )
            # Re-fetch with all relations
            full_package = get_submission_package_by_id(str(package.id))
            return Response(
                SubmissionPackageDetailSerializer(full_package).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class SubmissionPackageDetailAPIView(APIView):
    """Retrieve complete submission package detail, candidate roster, and dispatch history."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, package_id):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if not (user_roles & AUDIT_ROLES or request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Access denied. Placement staff role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        package = get_submission_package_by_id(str(package_id))
        if not package:
            raise Http404("Submission package not found.")

        return Response(SubmissionPackageDetailSerializer(package).data)


class SubmissionPackageGenerateRosterAPIView(APIView):
    """Generate standardized master XLSX spreadsheet with student metrics & SHA-256 digest (Step 25)."""

    permission_classes = [permissions.IsAuthenticated, CanManageSubmissions]

    def post(self, request, package_id):
        try:
            package = generate_candidate_roster_spreadsheet(str(package_id), user=request.user)
            full_package = get_submission_package_by_id(str(package.id))
            return Response(SubmissionPackageDetailSerializer(full_package).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class SubmissionPackageDownloadRosterAPIView(APIView):
    """Download the generated master XLSX candidate roster spreadsheet (Step 25)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, package_id):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if not (user_roles & AUDIT_ROLES or request.user.is_staff or request.user.is_superuser):
            return Response(
                {"detail": "Access denied. Placement staff role required."},
                status=status.HTTP_403_FORBIDDEN,
            )

        package = get_submission_package_by_id(str(package_id))
        if not package or not package.roster_file:
            raise Http404("Roster spreadsheet not found. Generate it first via Step 25.")

        response = FileResponse(
            package.roster_file.open("rb"),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = f'attachment; filename="{package.roster_file_name or "candidate_roster.xlsx"}"'
        return response


class SubmissionPackageAttachResumesAPIView(APIView):
    """Verify and lock certified resume PDF attachments for all roster candidates (Step 26)."""

    permission_classes = [permissions.IsAuthenticated, CanManageSubmissions]

    def post(self, request, package_id):
        try:
            package = verify_and_attach_resumes(str(package_id), user=request.user)
            full_package = get_submission_package_by_id(str(package.id))
            return Response(SubmissionPackageDetailSerializer(full_package).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class SubmissionPackageDispatchAPIView(APIView):
    """Send candidate profiles to corporate HR with transmission logging (Step 27)."""

    permission_classes = [permissions.IsAuthenticated, CanManageSubmissions]

    def post(self, request, package_id):
        serializer = DispatchPackageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            package = dispatch_candidate_profiles_to_hr(
                package_id=str(package_id),
                user=request.user,
                channel=vd.get("channel", "EMAIL"),
                recipient_email=vd.get("recipient_email", ""),
                recipient_name=vd.get("recipient_name", ""),
                recipient_phone=vd.get("recipient_phone", ""),
                dispatch_notes=vd.get("dispatch_notes", ""),
            )
            full_package = get_submission_package_by_id(str(package.id))
            return Response(SubmissionPackageDetailSerializer(full_package).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class SubmissionPackageAcknowledgeAPIView(APIView):
    """Record corporate recruiter receipt acknowledgment, feedback, and drive timeline (Step 28)."""

    permission_classes = [permissions.IsAuthenticated, CanAcknowledgeSubmissions]

    def post(self, request, package_id):
        serializer = RecordAcknowledgementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            package = record_company_acknowledgement(
                package_id=str(package_id),
                user=request.user,
                acknowledged_by_contact_name=vd["acknowledged_by_contact_name"],
                acknowledgement_channel=vd.get("acknowledgement_channel", "EMAIL"),
                recruiter_feedback=vd.get("recruiter_feedback", ""),
                tentative_interview_date=vd.get("tentative_interview_date"),
                follow_up_callback_date=vd.get("follow_up_callback_date"),
            )
            full_package = get_submission_package_by_id(str(package.id))
            return Response(SubmissionPackageDetailSerializer(full_package).data)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class StudentSubmissionsListAPIView(APIView):
    """Student views their own drive submissions with strict candidate isolation."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        submissions = get_student_submissions(request.user)
        serializer = StudentSubmissionSerializer(submissions, many=True)
        return Response(serializer.data)
