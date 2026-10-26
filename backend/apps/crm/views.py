"""DRF Views and ViewSets for Corporate CRM & HR Directory."""
from typing import Any
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.pagination import StandardResultsSetPagination
from apps.crm.models import CRMConfiguration, Company, FollowUp, HRContact, OutreachLog
from apps.crm.permissions import IsCRMManagerOrAdmin, IsCRMStaffOrAuditor
from apps.crm.selectors import (
    check_company_duplicates,
    check_hr_contact_duplicates,
    get_companies_queryset,
    get_crm_dashboard_metrics,
    get_follow_ups_queryset,
    get_hr_contacts_queryset,
    get_outreach_logs_queryset,
)
from apps.crm.serializers import (
    CompanyCreateUpdateSerializer,
    CompanyDetailSerializer,
    CompanyDuplicateCheckSerializer,
    CompanyListSerializer,
    FollowUpCancelSerializer,
    FollowUpCompleteSerializer,
    FollowUpCreateSerializer,
    FollowUpReopenSerializer,
    FollowUpRescheduleSerializer,
    FollowUpSerializer,
    HRContactCreateUpdateSerializer,
    HRContactDetailSerializer,
    HRContactListSerializer,
    OutreachLogCreateSerializer,
    OutreachLogSerializer,
)
from apps.crm.services import (
    archive_company,
    archive_hr_contact,
    cancel_follow_up,
    complete_follow_up,
    create_company,
    create_hr_contact,
    record_outreach_activity,
    reopen_follow_up,
    reschedule_follow_up,
    restore_company,
    restore_hr_contact,
    schedule_follow_up,
    update_company,
    update_hr_contact,
)


@extend_schema_view(
    list=extend_schema(summary="List corporate companies with filtering"),
    retrieve=extend_schema(summary="Retrieve full company profile"),
    create=extend_schema(summary="Create a new corporate company"),
    update=extend_schema(summary="Update company details"),
    partial_update=extend_schema(summary="Partially update company"),
)
class CompanyViewSet(viewsets.ModelViewSet):
    """Corporate enterprise profiles and hiring partner lifecycle management."""

    permission_classes = [IsCRMStaffOrAuditor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params
        is_archived_param = params.get("is_archived")
        is_archived = None
        if is_archived_param is not None:
            is_archived = is_archived_param.lower() in ("true", "1", "yes")

        return get_companies_queryset(
            search=params.get("search"),
            domain_category=params.get("domain_category"),
            relationship_status=params.get("relationship_status"),
            tier=params.get("tier"),
            city=params.get("city"),
            owner_id=params.get("owner_id"),
            is_archived=is_archived,
            ordering=params.get("ordering", "name"),
        )

    def get_serializer_class(self):
        if self.action == "list":
            return CompanyListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CompanyCreateUpdateSerializer
        return CompanyDetailSerializer

    def perform_create(self, serializer):
        company = create_company(self.request.user, serializer.validated_data)
        serializer.instance = company

    def perform_update(self, serializer):
        company = update_company(
            self.request.user, serializer.instance, serializer.validated_data
        )
        serializer.instance = company

    @extend_schema(summary="Cautiously check duplicate company warnings")
    @action(detail=False, methods=["get"], url_path="check-duplicate")
    def check_duplicate(self, request: Request) -> Response:
        serializer = CompanyDuplicateCheckSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        matches = check_company_duplicates(
            name=serializer.validated_data["name"],
            website=serializer.validated_data.get("website", ""),
        )
        return Response({"success": True, "data": matches})

    @extend_schema(summary="Archive corporate company")
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        archive_company(request.user, company)
        return Response({"success": True, "message": f"Company '{company.name}' archived."})

    @extend_schema(summary="Restore corporate company")
    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        restore_company(request.user, company)
        return Response({"success": True, "message": f"Company '{company.name}' restored."})

    @extend_schema(summary="List contacts for this company")
    @action(detail=True, methods=["get"], url_path="contacts")
    def contacts(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        contacts_qs = get_hr_contacts_queryset(company_id=company.id)
        page = self.paginate_queryset(contacts_qs)
        if page is not None:
            serializer = HRContactListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = HRContactListSerializer(contacts_qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="List outreach history for this company")
    @action(detail=True, methods=["get"], url_path="outreach")
    def outreach(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        outreach_qs = get_outreach_logs_queryset(company_id=company.id)
        page = self.paginate_queryset(outreach_qs)
        if page is not None:
            serializer = OutreachLogSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = OutreachLogSerializer(outreach_qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="List follow-ups for this company")
    @action(detail=True, methods=["get"], url_path="follow-ups")
    def follow_ups(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        follow_ups_qs = get_follow_ups_queryset(company_id=company.id)
        page = self.paginate_queryset(follow_ups_qs)
        if page is not None:
            serializer = FollowUpSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowUpSerializer(follow_ups_qs, many=True)
        return Response({"success": True, "data": serializer.data})


@extend_schema_view(
    list=extend_schema(summary="List HR talent contacts with filtering"),
    retrieve=extend_schema(summary="Retrieve HR contact details"),
    create=extend_schema(summary="Create a new HR contact"),
    update=extend_schema(summary="Update an HR contact"),
    partial_update=extend_schema(summary="Partially update an HR contact"),
)
class HRContactViewSet(viewsets.ModelViewSet):
    """Corporate HR talent leads and recruitment decision makers."""

    permission_classes = [IsCRMStaffOrAuditor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params
        is_archived_param = params.get("is_archived")
        is_archived = None
        if is_archived_param is not None:
            is_archived = is_archived_param.lower() in ("true", "1", "yes")

        return get_hr_contacts_queryset(
            company_id=params.get("company_id"),
            search=params.get("search"),
            status=params.get("status"),
            owner_id=params.get("owner_id"),
            is_archived=is_archived,
            ordering=params.get("ordering", "name"),
        )

    def get_serializer_class(self):
        if self.action == "list":
            return HRContactListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return HRContactCreateUpdateSerializer
        return HRContactDetailSerializer

    def perform_create(self, serializer):
        contact = create_hr_contact(self.request.user, serializer.validated_data)
        serializer.instance = contact

    def perform_update(self, serializer):
        contact = update_hr_contact(
            self.request.user, serializer.instance, serializer.validated_data
        )
        serializer.instance = contact

    @extend_schema(summary="Check duplicate HR contact within company")
    @action(detail=False, methods=["get"], url_path="check-duplicate")
    def check_duplicate(self, request: Request) -> Response:
        company_id = request.query_params.get("company_id")
        email = request.query_params.get("email")
        phone = request.query_params.get("phone")
        matches = check_hr_contact_duplicates(company_id=company_id, email=email, phone=phone)
        return Response({"success": True, "data": matches})

    @extend_schema(summary="Archive HR contact")
    @action(detail=True, methods=["post"], url_path="archive")
    def archive(self, request: Request, pk=None) -> Response:
        contact = self.get_object()
        archive_hr_contact(request.user, contact)
        return Response({"success": True, "message": f"Contact '{contact.name}' archived."})

    @extend_schema(summary="Restore HR contact")
    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request: Request, pk=None) -> Response:
        contact = self.get_object()
        restore_hr_contact(request.user, contact)
        return Response({"success": True, "message": f"Contact '{contact.name}' restored."})


@extend_schema_view(
    list=extend_schema(summary="List outreach touchpoints history"),
    retrieve=extend_schema(summary="Retrieve an outreach activity record"),
    create=extend_schema(summary="Record a completed outreach touchpoint"),
)
class OutreachLogViewSet(viewsets.ModelViewSet):
    """Multi-channel corporate relationship outreach activity log (Append-Only)."""

    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsCRMStaffOrAuditor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params
        return get_outreach_logs_queryset(
            company_id=params.get("company_id"),
            hr_contact_id=params.get("hr_contact_id"),
            performed_by_id=params.get("performed_by_id"),
            channel=params.get("channel"),
            outcome=params.get("outcome"),
            direction=params.get("direction"),
            date_from=params.get("date_from"),
            date_to=params.get("date_to"),
            search=params.get("search"),
        )

    def get_serializer_class(self):
        if self.action == "create":
            return OutreachLogCreateSerializer
        return OutreachLogSerializer

    def perform_create(self, serializer):
        outreach = record_outreach_activity(self.request.user, serializer.validated_data)
        serializer.instance = outreach


@extend_schema_view(
    list=extend_schema(summary="List scheduled corporate follow-ups"),
    retrieve=extend_schema(summary="Retrieve follow-up details"),
    create=extend_schema(summary="Schedule a corporate follow-up"),
)
class FollowUpViewSet(viewsets.ModelViewSet):
    """Corporate relationship follow-up queue and lifecycle management."""

    permission_classes = [IsCRMStaffOrAuditor]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        params = self.request.query_params
        is_overdue_param = params.get("is_overdue")
        is_overdue = None
        if is_overdue_param is not None:
            is_overdue = is_overdue_param.lower() in ("true", "1", "yes")

        return get_follow_ups_queryset(
            company_id=params.get("company_id"),
            hr_contact_id=params.get("hr_contact_id"),
            assigned_to_id=params.get("assigned_to_id"),
            status=params.get("status"),
            priority=params.get("priority"),
            is_overdue=is_overdue,
            due_date_from=params.get("due_date_from"),
            due_date_to=params.get("due_date_to"),
            search=params.get("search"),
        )

    def get_serializer_class(self):
        if self.action == "create":
            return FollowUpCreateSerializer
        return FollowUpSerializer

    def perform_create(self, serializer):
        follow_up = schedule_follow_up(self.request.user, serializer.validated_data)
        serializer.instance = follow_up

    @extend_schema(summary="Reschedule an open or in-progress follow-up")
    @action(detail=True, methods=["post"], url_path="reschedule")
    def reschedule(self, request: Request, pk=None) -> Response:
        follow_up = self.get_object()
        serializer = FollowUpRescheduleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = reschedule_follow_up(
            user=request.user,
            follow_up=follow_up,
            new_due_date=serializer.validated_data["new_due_date"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"success": True, "data": FollowUpSerializer(updated).data})

    @extend_schema(summary="Complete a follow-up task")
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request: Request, pk=None) -> Response:
        follow_up = self.get_object()
        serializer = FollowUpCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        completed = complete_follow_up(
            user=request.user,
            follow_up=follow_up,
            completion_notes=serializer.validated_data.get("completion_notes", ""),
        )
        return Response({"success": True, "data": FollowUpSerializer(completed).data})

    @extend_schema(summary="Cancel a follow-up task")
    @action(detail=True, methods=["post"], url_path="cancel")
    def cancel(self, request: Request, pk=None) -> Response:
        follow_up = self.get_object()
        serializer = FollowUpCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cancelled = cancel_follow_up(
            user=request.user,
            follow_up=follow_up,
            cancellation_reason=serializer.validated_data["cancellation_reason"],
        )
        return Response({"success": True, "data": FollowUpSerializer(cancelled).data})

    @extend_schema(summary="Reopen an authorized follow-up task")
    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request: Request, pk=None) -> Response:
        follow_up = self.get_object()
        serializer = FollowUpReopenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reopened = reopen_follow_up(
            user=request.user,
            follow_up=follow_up,
            new_due_date=serializer.validated_data["new_due_date"],
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response({"success": True, "data": FollowUpSerializer(reopened).data})

    @extend_schema(summary="List currently overdue follow-ups")
    @action(detail=False, methods=["get"], url_path="overdue")
    def overdue(self, request: Request) -> Response:
        overdue_qs = get_follow_ups_queryset(is_overdue=True)
        page = self.paginate_queryset(overdue_qs)
        if page is not None:
            serializer = FollowUpSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = FollowUpSerializer(overdue_qs, many=True)
        return Response({"success": True, "data": serializer.data})


class CRMDashboardMetricsView(APIView):
    """Permission-aware CRM operational metrics and target tracking."""

    permission_classes = [IsCRMStaffOrAuditor]

    @extend_schema(summary="Retrieve CRM dashboard KPIs, daily target progress, and recent activity")
    def get(self, request: Request) -> Response:
        tz_name = request.query_params.get("timezone", "Asia/Kolkata")
        metrics = get_crm_dashboard_metrics(request.user, timezone_name=tz_name)
        return Response({"success": True, "data": metrics})


class CRMConfigurationView(APIView):
    """Retrieve and manage CRM operational targets such as the 100+ outreach/day target."""

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsCRMStaffOrAuditor()]
        return [IsCRMManagerOrAdmin()]

    @extend_schema(summary="Get CRM operational configurations")
    def get(self, request: Request) -> Response:
        configs = CRMConfiguration.objects.all().values("key", "value", "description", "updated_at")
        config_map = {item["key"]: item["value"] for item in configs}
        return Response({"success": True, "data": config_map})

    @extend_schema(summary="Update CRM operational configuration")
    def post(self, request: Request) -> Response:
        key = request.data.get("key")
        value = request.data.get("value")
        if not key or value is None:
            return Response(
                {"success": False, "error": {"message": "'key' and 'value' are required."}},
                status=status.HTTP_400_BAD_REQUEST,
            )
        config, _ = CRMConfiguration.objects.update_or_create(
            key=key,
            defaults={"value": str(value)},
        )
        return Response({"success": True, "data": {"key": config.key, "value": config.value}})
