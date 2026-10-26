"""DRF Views and ViewSets for Job Requirements & Verification (Phase 3)."""
from typing import Any
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.models import JobRequirement
from apps.jobs.permissions import (
    CanApproveJobRequirement,
    CanVerifyJobChecklist,
    IsJobStaffOrAuditor,
)
from apps.jobs.selectors import (
    get_job_by_id,
    get_job_metrics,
    get_jobs_queryset,
    get_pending_approvals_queryset,
    get_pending_verifications_queryset,
)
from apps.jobs.serializers import (
    ChecklistItemVerifySerializer,
    JobActionReasonSerializer,
    JobApprovalDecisionSerializer,
    JobApprovalSerializer,
    JobChecklistItemSerializer,
    JobRequirementCreateUpdateSerializer,
    JobRequirementDetailSerializer,
    JobRequirementListSerializer,
)
from apps.jobs.services import (
    approve_job_requirement,
    archive_job_requirement,
    create_job_requirement,
    reject_job_requirement,
    reopen_job_requirement,
    restore_job_requirement,
    return_for_correction,
    submit_for_verification,
    update_job_requirement,
    verify_checklist_item,
)


@extend_schema_view(
    list=extend_schema(summary="List job requirements with search, filters, and pagination"),
    retrieve=extend_schema(summary="Retrieve full job requirement with checklist and decision log"),
    create=extend_schema(summary="Create a new job requirement draft"),
    partial_update=extend_schema(summary="Update editable draft or returned requirement"),
)
class JobRequirementViewSet(viewsets.ModelViewSet):
    """Manages job requirements, 5-point verification checklist, and approval gating (Steps 5–7)."""

    permission_classes = [IsJobStaffOrAuditor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params
        filters = {}
        if params.get("company"):
            filters["company_id"] = params.get("company")
        if params.get("status"):
            filters["status"] = params.get("status")
        if params.get("employment_type"):
            filters["employment_type"] = params.get("employment_type")
        if params.get("work_arrangement"):
            filters["work_arrangement"] = params.get("work_arrangement")
        if params.get("search"):
            filters["search"] = params.get("search")
        if params.get("assigned_verifier"):
            filters["assigned_verifier_id"] = params.get("assigned_verifier")
        if params.get("created_by"):
            filters["created_by_id"] = params.get("created_by")

        ordering = params.get("ordering", "-created_at")
        include_archived = params.get("include_archived", "").lower() in ("true", "1", "yes")

        return get_jobs_queryset(filters=filters, ordering=ordering, include_archived=include_archived)

    def get_serializer_class(self):
        if self.action == "list":
            return JobRequirementListSerializer
        if self.action in ("create", "update", "partial_update"):
            return JobRequirementCreateUpdateSerializer
        return JobRequirementDetailSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        job = create_job_requirement(
            company=data["company"],
            title=data["title"],
            job_description=data["job_description"],
            skills_required=data["skills_required"],
            location=data["location"],
            registration_deadline=data["registration_deadline"],
            created_by=request.user,
            hr_contact=data.get("hr_contact"),
            min_salary=data.get("min_salary"),
            max_salary=data.get("max_salary"),
            salary_currency=data.get("salary_currency", "INR"),
            salary_breakup=data.get("salary_breakup", ""),
            work_arrangement=data.get("work_arrangement", "ON_SITE"),
            employment_type=data.get("employment_type", "FULL_TIME"),
            has_bond=data.get("has_bond", False),
            bond_details=data.get("bond_details", ""),
            eligibility_criteria=data.get("eligibility_criteria", ""),
            min_cgpa=data.get("min_cgpa"),
            hiring_process=data.get("hiring_process", ""),
            interview_date=data.get("interview_date"),
            openings_count=data.get("openings_count", 1),
            notes=data.get("notes", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        detail_serializer = JobRequirementDetailSerializer(job)
        return Response(detail_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return self.partial_update(request, *args, **kwargs)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        job = self.get_object()
        serializer = self.get_serializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated_job = update_job_requirement(
            job=job,
            updated_by=request.user,
            data=serializer.validated_data,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @action(detail=True, methods=["post"], url_path="submit-verification")
    def submit_verification(self, request: Request, pk: str = None) -> Response:
        """Submit draft or corrected requirement for verification (Step 6)."""
        job = self.get_object()
        comments = request.data.get("comments", "")
        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated_job = submit_for_verification(
            job=job,
            user=request.user,
            comments=comments,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"checklist/(?P<item_id>[^/.]+)/verify",
        permission_classes=[CanVerifyJobChecklist],
    )
    def verify_checklist(self, request: Request, pk: str = None, item_id: str = None) -> Response:
        """Verify an individual checklist item (Step 6)."""
        job = self.get_object()
        serializer = ChecklistItemVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        item = verify_checklist_item(
            job=job,
            item_id=item_id,
            status=serializer.validated_data["status"],
            user=request.user,
            remarks=serializer.validated_data.get("remarks", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        # Return updated job detail so client receives refreshed status and checklist
        job.refresh_from_db()
        return Response(JobRequirementDetailSerializer(job).data)

    @action(detail=True, methods=["post"], url_path="return-correction")
    def return_correction(self, request: Request, pk: str = None) -> Response:
        """Return requirement to creator for corrections."""
        job = self.get_object()
        serializer = JobActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated_job = return_for_correction(
            job=job,
            user=request.user,
            reason=serializer.validated_data["reason"],
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(updated_job).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="approve",
        permission_classes=[CanApproveJobRequirement],
    )
    def approve(self, request: Request, pk: str = None) -> Response:
        """Formal sign-off gate (Step 7) by Placement Head or Admin."""
        job = self.get_object()
        serializer = JobApprovalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        approved_job = approve_job_requirement(
            job=job,
            approver=request.user,
            comments=serializer.validated_data.get("comments", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(approved_job).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="reject",
        permission_classes=[CanApproveJobRequirement],
    )
    def reject(self, request: Request, pk: str = None) -> Response:
        """Formally decline opportunity (Step 7)."""
        job = self.get_object()
        serializer = JobActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        rejected_job = reject_job_requirement(
            job=job,
            user=request.user,
            rejection_reason=serializer.validated_data["reason"],
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(rejected_job).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="reopen",
        permission_classes=[CanApproveJobRequirement],
    )
    def reopen(self, request: Request, pk: str = None) -> Response:
        """Reopen locked or rejected requirement for re-audit."""
        job = self.get_object()
        serializer = JobActionReasonSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        reopened_job = reopen_job_requirement(
            job=job,
            user=request.user,
            comments=serializer.validated_data["reason"],
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(JobRequirementDetailSerializer(reopened_job).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="archive",
        permission_classes=[CanApproveJobRequirement],
    )
    def archive(self, request: Request, pk: str = None) -> Response:
        """Soft-archive a job requirement."""
        job = self.get_object()
        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        archived = archive_job_requirement(
            job=job, user=request.user, correlation_id=correlation_id, ip_address=ip_address
        )
        return Response(JobRequirementDetailSerializer(archived).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="restore",
        permission_classes=[CanApproveJobRequirement],
    )
    def restore(self, request: Request, pk: str = None) -> Response:
        """Restore an archived job requirement."""
        job = self.get_object()
        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        restored = restore_job_requirement(
            job=job, user=request.user, correlation_id=correlation_id, ip_address=ip_address
        )
        return Response(JobRequirementDetailSerializer(restored).data)

    @action(detail=False, methods=["get"], url_path="pending-verification")
    def pending_verification(self, request: Request) -> Response:
        """Queue of job opportunities awaiting checklist verification (Step 6)."""
        qs = get_pending_verifications_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = JobRequirementListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = JobRequirementListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="pending-approval")
    def pending_approval(self, request: Request) -> Response:
        """Queue of verified opportunities awaiting Placement Head sign-off (Step 7)."""
        qs = get_pending_approvals_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = JobRequirementListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = JobRequirementListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="metrics")
    def metrics(self, request: Request) -> Response:
        """Dashboard metrics for job requirement lifecycle."""
        data = get_job_metrics()
        return Response(data)
