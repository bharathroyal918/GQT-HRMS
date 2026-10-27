"""DRF ViewSets and API Views for Placement Management & Tracking (Workflow Steps 36-41)."""
from django.http import Http404, FileResponse
from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.placements.permissions import (
    CanManagePlacements,
    CanManageOfferLetters,
    IsStudentOrStaffPlacementAccess,
    AUDIT_ROLES,
)
from apps.placements import selectors, services
from apps.placements.serializers import (
    FinalResultIntakeSerializer,
    FinalResultIntakeCreateSerializer,
    CandidatePlacementStatusSerializer,
    CandidatePlacementStatusDetailSerializer,
    UpdatePlacementStatusPayloadSerializer,
    PlacementNotificationLogSerializer,
    CandidateOfferLetterSerializer,
    OfferLetterUploadPayloadSerializer,
    OfferAcceptancePayloadSerializer,
    JoiningStatusUpdatePayloadSerializer,
    StudentPlacementViewSerializer,
)


class FinalResultIntakeViewSet(viewsets.ViewSet):
    """API endpoints for HR Final Result Ingestion (Step 36)."""

    permission_classes = [permissions.IsAuthenticated, CanManagePlacements]

    def list(self, request):
        job_id = request.query_params.get("job_id")
        company_id = request.query_params.get("company_id")
        search = request.query_params.get("search")
        intakes = selectors.get_final_result_intakes(
            job_id=job_id,
            company_id=company_id,
            search=search,
        )
        serializer = FinalResultIntakeSerializer(intakes, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = FinalResultIntakeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            intake = services.receive_final_results(
                job_id=str(vd["job_requirement_id"]),
                company_id=str(vd["company_id"]),
                hr_contact_id=str(vd["hr_contact_id"]) if vd.get("hr_contact_id") else None,
                candidate_results=vd["candidate_results"],
                source=vd.get("source", "EMAIL"),
                received_at=vd.get("received_at"),
                notes=vd.get("notes", ""),
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = FinalResultIntakeSerializer(intake)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        intake = selectors.get_final_result_intake_by_id(pk)
        if not intake:
            return Response({"detail": "Final result intake batch not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = FinalResultIntakeSerializer(intake)
        return Response(serializer.data)


class CandidatePlacementStatusViewSet(viewsets.ViewSet):
    """API endpoints for Candidate Placement Status and Notifications (Steps 37 & 38)."""

    def get_permissions(self):
        if self.action in ["update_status", "notify"]:
            return [permissions.IsAuthenticated(), CanManagePlacements()]
        return [permissions.IsAuthenticated(), IsStudentOrStaffPlacementAccess()]

    def list(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        is_staff = bool(user_roles & AUDIT_ROLES) or request.user.is_staff or request.user.is_superuser

        student_id = request.query_params.get("student_id")
        if not is_staff:
            profile = getattr(request.user, "student_profile", None)
            if not profile:
                return Response([])
            student_id = str(profile.id)

        statuses = selectors.get_candidate_placement_statuses(
            job_id=request.query_params.get("job_id"),
            company_id=request.query_params.get("company_id"),
            student_id=student_id,
            status=request.query_params.get("status"),
            search=request.query_params.get("search"),
        )
        serializer = CandidatePlacementStatusSerializer(statuses, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        placement = selectors.get_candidate_placement_status_by_id(pk)
        if not placement:
            return Response({"detail": "Candidate placement record not found."}, status=status.HTTP_404_NOT_FOUND)

        # Object-level permission check
        self.check_object_permissions(request, placement)

        serializer = CandidatePlacementStatusDetailSerializer(placement)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"], url_path="update-status")
    def update_status(self, request, pk=None):
        """Update candidate placement status with server-side validation and audit log (Step 37)."""
        serializer = UpdatePlacementStatusPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            placement = services.update_candidate_placement_status(
                placement_id=pk,
                new_status=vd["status"],
                reason=vd.get("reason", ""),
                designation_offered=vd.get("designation_offered"),
                offered_ctc=vd.get("offered_ctc"),
                work_location=vd.get("work_location"),
                remarks=vd.get("remarks"),
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = CandidatePlacementStatusDetailSerializer(placement)
        return Response(out_serializer.data)

    @action(detail=True, methods=["POST"], url_path="notify")
    def notify(self, request, pk=None):
        """Dispatch truthful candidate notification for their placement outcome (Step 38)."""
        channel = request.data.get("channel", "EMAIL")
        try:
            log = services.notify_candidate_placement_status(
                placement_id=pk,
                channel=channel,
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = PlacementNotificationLogSerializer(log)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)


class CandidateOfferLetterViewSet(viewsets.ViewSet):
    """API endpoints for Offer Letters, Acceptance, and Joining Verification (Steps 39, 40, 41)."""

    def get_permissions(self):
        if self.action in ["upload_offer"]:
            return [permissions.IsAuthenticated(), CanManageOfferLetters()]
        if self.action in ["verify_joining"]:
            return [permissions.IsAuthenticated(), CanManagePlacements()]
        return [permissions.IsAuthenticated(), IsStudentOrStaffPlacementAccess()]

    def list(self, request):
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        is_staff = bool(user_roles & AUDIT_ROLES) or request.user.is_staff or request.user.is_superuser

        student_id = request.query_params.get("student_id")
        if not is_staff:
            profile = getattr(request.user, "student_profile", None)
            if not profile:
                return Response([])
            student_id = str(profile.id)

        offers = selectors.get_candidate_offer_letters(
            job_id=request.query_params.get("job_id"),
            company_id=request.query_params.get("company_id"),
            student_id=student_id,
            acceptance_status=request.query_params.get("acceptance_status"),
            joining_status=request.query_params.get("joining_status"),
            search=request.query_params.get("search"),
        )
        serializer = CandidateOfferLetterSerializer(offers, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        offer = selectors.get_offer_letter_by_id(pk)
        if not offer:
            return Response({"detail": "Offer letter record not found."}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, offer)
        serializer = CandidateOfferLetterSerializer(offer)
        return Response(serializer.data)

    @action(detail=False, methods=["POST"], url_path="upload-offer")
    def upload_offer(self, request):
        """Upload official offer letter PDF for selected candidate (Step 39)."""
        serializer = OfferLetterUploadPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            offer = services.upload_offer_letter(
                placement_id=str(vd["placement_id"]),
                file_obj=vd["file"],
                acceptance_deadline=vd.get("acceptance_deadline"),
                expected_joining_date=vd.get("expected_joining_date"),
                joining_location=vd.get("joining_location", ""),
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = CandidateOfferLetterSerializer(offer)
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["POST"], url_path="respond")
    def respond(self, request, pk=None):
        """Candidate self-service or staff-recorded response to offer letter (Step 40)."""
        offer = selectors.get_offer_letter_by_id(pk)
        if not offer:
            return Response({"detail": "Offer letter record not found."}, status=status.HTTP_404_NOT_FOUND)

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        is_staff = bool(user_roles & AUDIT_ROLES) or request.user.is_staff or request.user.is_superuser

        # If not staff, enforce that the student responding is the owner of the offer
        if not is_staff:
            if offer.student.user != request.user:
                return Response(
                    {"detail": "Access denied. You cannot respond to another candidate's offer."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            source = "STUDENT_PORTAL"
        else:
            source = request.data.get("source", "PLACEMENT_OFFICE")

        serializer = OfferAcceptancePayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            updated_offer = services.record_offer_acceptance(
                offer_id=pk,
                decision=vd["decision"],
                notes=vd.get("notes", ""),
                source=source,
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = CandidateOfferLetterSerializer(updated_offer)
        return Response(out_serializer.data)

    @action(detail=True, methods=["POST"], url_path="verify-joining")
    def verify_joining(self, request, pk=None):
        """Verify candidate onboarding and joining status (Step 41)."""
        serializer = JoiningStatusUpdatePayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        try:
            offer = services.record_joining_status(
                offer_id=pk,
                joining_status=vd["joining_status"],
                actual_joining_date=vd.get("actual_joining_date"),
                deferred_joining_date=vd.get("deferred_joining_date"),
                joining_location=vd.get("joining_location", ""),
                employee_id_assigned=vd.get("employee_id_assigned", ""),
                notes=vd.get("notes", ""),
                user=request.user,
            )
        except ValidationError as e:
            return Response(
                {"detail": str(e.message if hasattr(e, "message") else e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        out_serializer = CandidateOfferLetterSerializer(offer)
        return Response(out_serializer.data)


class OfferLetterDownloadAPIView(APIView):
    """Private authenticated streaming download with strict object-level isolation (Step 39)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        offer = selectors.get_offer_letter_by_id(pk)
        if not offer:
            raise Http404("Offer letter record not found.")

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        is_staff = bool(user_roles & AUDIT_ROLES) or request.user.is_staff or request.user.is_superuser

        if not is_staff and offer.student.user != request.user:
            return Response(
                {"detail": "Access denied. Cannot access another student's offer letter document."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = FileResponse(offer.file.open("rb"), content_type="application/pdf")
        response["Content-Disposition"] = f'inline; filename="{offer.file_name or "offer_letter.pdf"}"'
        return response


class StudentPlacementAPIView(APIView):
    """Returns authenticated student's placement records and active offer letters."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = selectors.get_student_placement_records(request.user)
        serializer = StudentPlacementViewSerializer(records, many=True)
        return Response(serializer.data)


class PlacementKPIAPIView(APIView):
    """Returns aggregate placement KPIs."""

    permission_classes = [permissions.IsAuthenticated, CanManagePlacements]

    def get(self, request):
        kpis = selectors.get_placement_kpis()
        return Response(kpis)


class JobParticipatingCandidatesAPIView(APIView):
    """Returns participating candidates eligible for final result intake."""

    permission_classes = [permissions.IsAuthenticated, CanManagePlacements]

    def get(self, request, job_id):
        candidates = selectors.get_participated_candidates_for_job(job_id)
        return Response(candidates)
