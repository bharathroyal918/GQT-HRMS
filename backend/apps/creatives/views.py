"""DRF Views and ViewSets for Creative Studio & Promotional Assets Management (Phase 4)."""
import os
from typing import Any
from django.http import FileResponse, Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from apps.accounts.models import User
from apps.core.pagination import StandardResultsSetPagination
from apps.jobs.selectors import get_job_by_id
from apps.creatives.models import CreativeRequest
from apps.creatives.permissions import (
    IsCreativeStaffOrAuditor,
    CanAssignDesigner,
    CanVerifyCreativeChecklist,
    CanApproveCreative,
)
from apps.creatives.selectors import (
    get_creative_requests_queryset,
    get_creative_request_by_id,
    get_asset_version_by_id,
    get_designer_queue_queryset,
    get_pending_review_queue_queryset,
    get_creative_metrics,
)
from apps.creatives.serializers import (
    CreativeRequestListSerializer,
    CreativeRequestDetailSerializer,
    CreativeRequestCreateSerializer,
    CreativeBriefUpdateSerializer,
    AssignDesignerSerializer,
    UploadAssetVersionSerializer,
    CreativeAssetVersionSerializer,
    VerifyChecklistItemSerializer,
    CreativeChecklistItemSerializer,
    ReturnCorrectionSerializer,
    ApproveAssetVersionSerializer,
    RejectAssetVersionSerializer,
)
from apps.creatives.services import (
    create_creative_request,
    update_creative_brief,
    assign_designer,
    upload_asset_version,
    verify_checklist_item,
    return_for_correction,
    approve_asset_version,
    reject_asset_version,
    archive_creative_request,
    restore_creative_request,
)


@extend_schema_view(
    list=extend_schema(summary="List creative requests with filtering and pagination"),
    retrieve=extend_schema(summary="Retrieve full creative request with versions and decisions"),
    create=extend_schema(summary="Create a new creative request from an approved job"),
    partial_update=extend_schema(summary="Update an editable creative brief"),
)
class CreativeRequestViewSet(viewsets.ModelViewSet):
    """Manages promotional creative requests, asset versions, and 4-point design verification checklist (Steps 8–9)."""

    permission_classes = [IsCreativeStaffOrAuditor]
    pagination_class = StandardResultsSetPagination
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        params = self.request.query_params
        return get_creative_requests_queryset(
            user=self.request.user,
            company_id=params.get("company"),
            job_id=params.get("job"),
            status=params.get("status"),
            deliverable_type=params.get("deliverable_type"),
            priority=params.get("priority"),
            assigned_designer_id=params.get("assigned_designer"),
            search=params.get("search"),
            include_archived=params.get("include_archived", "").lower() in ("true", "1", "yes"),
            ordering=params.get("ordering", "-created_at"),
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CreativeRequestListSerializer
        if self.action == "create":
            return CreativeRequestCreateSerializer
        if self.action in ("update", "partial_update"):
            return CreativeBriefUpdateSerializer
        return CreativeRequestDetailSerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = CreativeRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        job = get_job_by_id(str(data["job_requirement_id"]))
        if not job:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Job requirement does not exist."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        assigned_designer = None
        if data.get("assigned_designer_id"):
            assigned_designer = User.objects.filter(id=data["assigned_designer_id"]).first()
            if not assigned_designer:
                return Response(
                    {"success": False, "error": {"code": "NOT_FOUND", "message": "Assigned designer not found."}},
                    status=status.HTTP_404_NOT_FOUND,
                )

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        creative_req = create_creative_request(
            job_requirement=job,
            user=request.user,
            title=data["title"],
            deliverable_type=data.get("deliverable_type"),
            priority=data.get("priority"),
            brief=data.get("brief", ""),
            target_audience=data.get("target_audience", ""),
            registration_link=data.get("registration_link", ""),
            qr_code_target_url=data.get("qr_code_target_url", ""),
            contact_email=data.get("contact_email", ""),
            contact_phone=data.get("contact_phone", ""),
            production_deadline=data.get("production_deadline"),
            assigned_designer=assigned_designer,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )

        output = CreativeRequestDetailSerializer(creative_req)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pk = kwargs.get("pk")
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")
        serializer = CreativeRequestDetailSerializer(creative_req)
        return Response(serializer.data)

    def partial_update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        pk = kwargs.get("pk")
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")

        serializer = CreativeBriefUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated = update_creative_brief(
            creative_req=creative_req,
            user=request.user,
            data=serializer.validated_data,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeRequestDetailSerializer(updated).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="assign",
        permission_classes=[IsAuthenticated, CanAssignDesigner],
    )
    def assign_designer_action(self, request: Request, pk: str = None) -> Response:
        """Assign or reassign a graphic designer to this request (Step 8)."""
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")

        serializer = AssignDesignerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        designer = User.objects.filter(id=serializer.validated_data["designer_id"]).first()
        if not designer:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Designer user not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated = assign_designer(
            creative_req=creative_req,
            designer=designer,
            assigned_by=request.user,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeRequestDetailSerializer(updated).data)

    @action(
        detail=True,
        methods=["post"],
        url_path="versions",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_version(self, request: Request, pk: str = None) -> Response:
        """Upload a promotional asset file version (Step 8 & 9)."""
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")

        serializer = UploadAssetVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        version = upload_asset_version(
            creative_req=creative_req,
            uploaded_file=data["file"],
            designer_user=request.user,
            deliverable_type=data.get("deliverable_type"),
            designer_notes=data.get("designer_notes", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )

        return Response(CreativeAssetVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path=r"versions/(?P<version_id>[^/.]+)")
    def get_version_detail(self, request: Request, pk: str = None, version_id: str = None) -> Response:
        """Retrieve details of a specific asset version with its 4-point checklist items."""
        version = get_asset_version_by_id(pk, version_id)
        if not version:
            raise Http404("Asset version not found.")
        return Response(CreativeAssetVersionSerializer(version).data)

    @action(detail=True, methods=["get"], url_path=r"versions/(?P<version_id>[^/.]+)/file")
    def download_asset_file(self, request: Request, pk: str = None, version_id: str = None):
        """Secure, authenticated streaming download of a promotional creative asset (Storage-Agnostic)."""
        version = get_asset_version_by_id(pk, version_id)
        if not version or not version.file:
            raise Http404("Asset version or file not found.")

        try:
            file_handle = version.file.open("rb")
        except (FileNotFoundError, OSError, ValueError):
            raise Http404("File not found on storage.")

        response = FileResponse(
            file_handle,
            content_type=version.mime_type or "application/octet-stream",
        )
        safe_filename = version.file_name or os.path.basename(version.file.name) or "creative_asset"
        response["Content-Disposition"] = f'inline; filename="{safe_filename}"'
        if version.file_size_bytes:
            response["Content-Length"] = version.file_size_bytes
        return response

    @action(
        detail=True,
        methods=["post"],
        url_path=r"versions/(?P<version_id>[^/.]+)/checklist/(?P<item_code>[^/.]+)/verify",
        permission_classes=[IsAuthenticated, CanVerifyCreativeChecklist],
    )
    def verify_checklist_action(
        self, request: Request, pk: str = None, version_id: str = None, item_code: str = None
    ) -> Response:
        """Verify an individual design checklist criterion (Step 9)."""
        version = get_asset_version_by_id(pk, version_id)
        if not version:
            raise Http404("Asset version not found.")

        serializer = VerifyChecklistItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        item = verify_checklist_item(
            version=version,
            item_code=item_code,
            status=data["status"],
            reviewer=request.user,
            remarks=data.get("remarks", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )

        return Response(CreativeChecklistItemSerializer(item).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"versions/(?P<version_id>[^/.]+)/return-correction",
        permission_classes=[IsAuthenticated, CanVerifyCreativeChecklist],
    )
    def return_correction_action(
        self, request: Request, pk: str = None, version_id: str = None
    ) -> Response:
        """Return an asset version to the designer for correction with mandatory feedback (Step 9)."""
        version = get_asset_version_by_id(pk, version_id)
        if not version:
            raise Http404("Asset version not found.")

        serializer = ReturnCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        updated = return_for_correction(
            version=version,
            reviewer=request.user,
            feedback=serializer.validated_data["feedback"],
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeAssetVersionSerializer(updated).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"versions/(?P<version_id>[^/.]+)/approve",
        permission_classes=[IsAuthenticated, CanApproveCreative],
    )
    def approve_version_action(
        self, request: Request, pk: str = None, version_id: str = None
    ) -> Response:
        """Step 9 Creative Approval Gate by Placement Head or System Administrator."""
        version = get_asset_version_by_id(pk, version_id)
        if not version:
            raise Http404("Asset version not found.")

        serializer = ApproveAssetVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        approved = approve_asset_version(
            version=version,
            approver=request.user,
            comments=serializer.validated_data.get("comments", ""),
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeAssetVersionSerializer(approved).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"versions/(?P<version_id>[^/.]+)/reject",
        permission_classes=[IsAuthenticated, CanApproveCreative],
    )
    def reject_version_action(
        self, request: Request, pk: str = None, version_id: str = None
    ) -> Response:
        """Formally reject a creative asset version."""
        version = get_asset_version_by_id(pk, version_id)
        if not version:
            raise Http404("Asset version not found.")

        serializer = RejectAssetVersionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        rejected = reject_asset_version(
            version=version,
            user=request.user,
            rejection_reason=serializer.validated_data["rejection_reason"],
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeAssetVersionSerializer(rejected).data)

    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request: Request, pk: str = None) -> Response:
        """Archive a creative request."""
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        archived = archive_creative_request(
            request=creative_req,
            user=request.user,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeRequestDetailSerializer(archived).data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request: Request, pk: str = None) -> Response:
        """Restore an archived creative request."""
        creative_req = get_creative_request_by_id(pk)
        if not creative_req:
            raise Http404("Creative request not found.")

        correlation_id = getattr(request, "correlation_id", "")
        ip_address = request.META.get("REMOTE_ADDR")

        restored = restore_creative_request(
            request=creative_req,
            user=request.user,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )
        return Response(CreativeRequestDetailSerializer(restored).data)

    @action(detail=False, methods=["get"], url_path="designer-queue")
    def designer_queue(self, request: Request) -> Response:
        """Operational queue of active requests assigned to the authenticated graphic designer."""
        qs = get_designer_queue_queryset(request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CreativeRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CreativeRequestListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="pending-review")
    def pending_review(self, request: Request) -> Response:
        """Operational review queue of creative requests awaiting verification or approval."""
        qs = get_pending_review_queue_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = CreativeRequestListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CreativeRequestListSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="metrics")
    def metrics(self, request: Request) -> Response:
        """Aggregate KPI metrics for Creative Studio."""
        data = get_creative_metrics()
        return Response(data)
