"""DRF Views and ViewSets for Corporate CRM & HR Directory."""
from typing import Any
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db.models import Q
from django.http import HttpResponse
from apps.core.pagination import StandardResultsSetPagination
from apps.crm.models import (
    CaseEscalation,
    CRMConfiguration,
    Company,
    CRMReconciliationRun,
    FollowUp,
    FollowUpReminderItem,
    HRContact,
    OutreachLog,
    StaffNotification,
)
from apps.crm.permissions import (
    CanAccessStudent360,
    CanManageCaseEscalations,
    CanManageCRMReconciliation,
    IsCRMManagerOrAdmin,
    IsCRMStaffOrAuditor,
)
from apps.crm.selectors import (
    check_company_duplicates,
    check_hr_contact_duplicates,
    get_case_escalations_queryset,
    get_companies_queryset,
    get_company_360_profile,
    get_company_communication_timeline,
    get_crm_dashboard_metrics,
    get_crm_database_health_diagnostics,
    get_follow_up_reminders_queryset,
    get_follow_ups_queryset,
    get_hr_contacts_queryset,
    get_outreach_logs_queryset,
    get_staff_notifications_queryset,
    get_student_360_profile,
    get_student_communication_timeline,
)
from apps.crm.serializers import (
    AutomationRunRequestSerializer,
    CaseEscalationAcknowledgeSerializer,
    CaseEscalationResolveSerializer,
    CaseEscalationSerializer,
    CompanyCreateUpdateSerializer,
    CompanyDetailSerializer,
    CompanyDuplicateCheckSerializer,
    CompanyListSerializer,
    CRMDatabaseHealthSerializer,
    CRMReconciliationRunSerializer,
    CRMReconciliationSyncRequestSerializer,
    FollowUpCancelSerializer,
    FollowUpCompleteSerializer,
    FollowUpCreateSerializer,
    FollowUpReminderItemSerializer,
    FollowUpReopenSerializer,
    FollowUpRescheduleSerializer,
    FollowUpSerializer,
    HRContactCreateUpdateSerializer,
    HRContactDetailSerializer,
    HRContactListSerializer,
    OutreachLogCreateSerializer,
    OutreachLogSerializer,
    StaffNotificationSerializer,
)
from apps.crm.services import (
    acknowledge_case_escalation,
    archive_company,
    archive_hr_contact,
    cancel_follow_up,
    complete_follow_up,
    create_company,
    create_hr_contact,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    record_outreach_activity,
    reopen_follow_up,
    reschedule_follow_up,
    resolve_case_escalation,
    restore_company,
    restore_hr_contact,
    retry_failed_reminder_item,
    run_crm_database_reconciliation,
    schedule_follow_up,
    update_company,
    update_hr_contact,
)
from apps.crm.scheduler import run_automated_followup_cycle



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

    @extend_schema(summary="Retrieve 360-degree recruitment integration profile for company")
    @action(detail=True, methods=["get"], url_path="360")
    def profile_360(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        data = get_company_360_profile(company.id)
        return Response({"success": True, "data": data})

    @extend_schema(summary="Retrieve chronological communication timeline for company")
    @action(detail=True, methods=["get"], url_path="timeline")
    def timeline(self, request: Request, pk=None) -> Response:
        company = self.get_object()
        events = get_company_communication_timeline(company.id)
        return Response({"success": True, "data": events})



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
            new_remind_at=serializer.validated_data.get("new_remind_at"),
        )
        return Response({"success": True, "data": FollowUpSerializer(updated).data})

    @extend_schema(summary="List automated reminder items for a follow-up")
    @action(detail=True, methods=["get"], url_path="reminders")
    def reminders(self, request: Request, pk=None) -> Response:
        follow_up = self.get_object()
        reminders_qs = follow_up.reminder_items.all().order_by("-scheduled_for")
        serializer = FollowUpReminderItemSerializer(reminders_qs, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(summary="Retry a failed automated reminder item")
    @action(detail=True, methods=["post"], url_path=r"reminders/(?P<reminder_id>[^/.]+)/retry")
    def retry_reminder(self, request: Request, pk=None, reminder_id=None) -> Response:
        follow_up = self.get_object()
        reminder_item = follow_up.reminder_items.filter(id=reminder_id).first()
        if not reminder_item:
            return Response(
                {"success": False, "error": {"message": "Reminder item not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        updated_item = retry_failed_reminder_item(request.user, reminder_item)
        return Response({"success": True, "data": FollowUpReminderItemSerializer(updated_item).data})

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


# ==============================================================================
# Phase 10: CRM Database Integration & Reconciliation Views
# ==============================================================================

class CRMReconciliationDiagnosticsView(APIView):
    """Retrieve 8-area database health diagnostics without modifying any data."""

    permission_classes = [CanManageCRMReconciliation]

    @extend_schema(summary="Audit 8-area CRM database health diagnostics")
    def get(self, request: Request) -> Response:
        report = get_crm_database_health_diagnostics()
        return Response({"success": True, "data": report})


class CRMReconciliationSyncView(APIView):
    """Execute safe, idempotent CRM database integration and reconciliation."""

    permission_classes = [CanManageCRMReconciliation]

    @extend_schema(summary="Run CRM database reconciliation")
    def post(self, request: Request) -> Response:
        serializer = CRMReconciliationSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dry_run = serializer.validated_data.get("dry_run", False)
        correlation_id = request.headers.get("X-Correlation-ID", "")
        result = run_crm_database_reconciliation(
            user=request.user,
            dry_run=dry_run,
            correlation_id=correlation_id,
        )
        return Response({"success": True, "data": result})


class CRMReconciliationHistoryView(APIView):
    """List historical audit records of CRM database reconciliation runs."""

    permission_classes = [CanManageCRMReconciliation]

    @extend_schema(summary="List CRM database reconciliation runs")
    def get(self, request: Request) -> Response:
        runs = CRMReconciliationRun.objects.select_related("triggered_by").order_by("-created_at")[:50]
        serializer = CRMReconciliationRunSerializer(runs, many=True)
        return Response({"success": True, "data": serializer.data})


class Student360View(APIView):
    """Retrieve 360-degree candidate profile integrating recruitment history."""

    permission_classes = [CanAccessStudent360]

    @extend_schema(summary="Retrieve 360-degree candidate profile")
    def get(self, request: Request, student_id: Any) -> Response:
        from apps.students.models import StudentProfile

        student = StudentProfile.objects.filter(
            Q(id=student_id) | Q(user_id=student_id), is_deleted=False
        ).select_related("user").first()
        if not student:
            return Response(
                {"success": False, "error": {"message": "Student profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, student)
        profile = get_student_360_profile(student.id, viewer_user=request.user)
        return Response({"success": True, "data": profile})


class StudentTimelineView(APIView):
    """Retrieve chronological communication history for candidate."""

    permission_classes = [CanAccessStudent360]

    @extend_schema(summary="Retrieve candidate communication history")
    def get(self, request: Request, student_id: Any) -> Response:
        from apps.students.models import StudentProfile

        student = StudentProfile.objects.filter(
            Q(id=student_id) | Q(user_id=student_id), is_deleted=False
        ).select_related("user").first()
        if not student:
            return Response(
                {"success": False, "error": {"message": "Student profile not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        self.check_object_permissions(request, student)
        events = get_student_communication_timeline(student.id)
        return Response({"success": True, "data": events})


# ==============================================================================
# Phase 12: Automated Follow-Up & Escalation Views
# ==============================================================================

@extend_schema_view(
    list=extend_schema(summary="List filterable case escalations"),
    retrieve=extend_schema(summary="Retrieve case escalation detail"),
)
class CaseEscalationViewSet(viewsets.ReadOnlyModelViewSet):
    """Auditable case escalation management (Phase 12 / Capability E)."""

    permission_classes = [CanManageCaseEscalations]
    pagination_class = StandardResultsSetPagination
    serializer_class = CaseEscalationSerializer

    def get_queryset(self):
        params = self.request.query_params
        return get_case_escalations_queryset(
            user=self.request.user,
            case_type=params.get("case_type"),
            status=params.get("status"),
            follow_up_id=params.get("follow_up_id"),
            date_from=params.get("date_from"),
            date_to=params.get("date_to"),
            search=params.get("search"),
        )

    @extend_schema(summary="Acknowledge a pending case escalation")
    @action(detail=True, methods=["post"], url_path="acknowledge")
    def acknowledge(self, request: Request, pk=None) -> Response:
        escalation = self.get_object()
        serializer = CaseEscalationAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = acknowledge_case_escalation(
            user=request.user,
            escalation=escalation,
            notes=serializer.validated_data.get("notes", ""),
        )
        return Response({"success": True, "data": CaseEscalationSerializer(updated).data})

    @extend_schema(summary="Resolve a case escalation with documented outcome")
    @action(detail=True, methods=["post"], url_path="resolve")
    def resolve(self, request: Request, pk=None) -> Response:
        escalation = self.get_object()
        serializer = CaseEscalationResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = resolve_case_escalation(
            user=request.user,
            escalation=escalation,
            resolution_notes=serializer.validated_data["resolution_notes"],
        )
        return Response({"success": True, "data": CaseEscalationSerializer(updated).data})


@extend_schema_view(
    list=extend_schema(summary="List in-app alerts and notifications for current user"),
    retrieve=extend_schema(summary="Retrieve an in-app notification"),
)
class StaffNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """In-app alerts and notifications for Placement Officers and Staff (Capability D)."""

    from rest_framework.permissions import IsAuthenticated
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    serializer_class = StaffNotificationSerializer

    def get_queryset(self):
        params = self.request.query_params
        is_read_param = params.get("is_read")
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() in ("true", "1", "yes")

        return get_staff_notifications_queryset(
            user=self.request.user,
            is_read=is_read,
            notification_type=params.get("notification_type"),
        )

    @extend_schema(summary="Mark notification as read")
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request: Request, pk=None) -> Response:
        notification = self.get_object()
        updated = mark_notification_as_read(request.user, notification)
        return Response({"success": True, "data": StaffNotificationSerializer(updated).data})

    @extend_schema(summary="Mark all unread notifications as read")
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request: Request) -> Response:
        count = mark_all_notifications_as_read(request.user)
        return Response({"success": True, "count": count})

    @extend_schema(summary="Get unread notification count for badge")
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request: Request) -> Response:
        count = StaffNotification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({"success": True, "count": count})


class CRMAutomationRunView(APIView):
    """Operational API trigger for executing the automated follow-up worker cycle."""

    permission_classes = [IsCRMStaffOrAuditor]

    @extend_schema(summary="Trigger automated follow-up execution cycle")
    def post(self, request: Request) -> Response:
        from apps.accounts.models import RoleCatalog
        if request.user.has_role(RoleCatalog.AUDITOR):
            return Response(
                {"success": False, "error": {"message": "Auditors cannot trigger automation runs."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = AutomationRunRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dry_run = serializer.validated_data.get("dry_run", False)

        results = run_automated_followup_cycle(
            dry_run=dry_run,
            triggered_by=request.user,
            correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response({"success": True, "data": results})


class WhatsAppWebhookView(APIView):
    """Meta WhatsApp Cloud API Webhook endpoint with verification challenge and delivery callbacks."""

    permission_classes = []  # AllowAny external webhook

    def get(self, request: Request) -> HttpResponse:
        """Handle Meta Webhook challenge verification with fail-closed security."""
        import hmac
        import os
        from django.conf import settings

        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge", "")

        is_production = (
            getattr(settings, "ENVIRONMENT", "").lower() == "production"
            or not getattr(settings, "DEBUG", True)
        )
        expected_token = (
            getattr(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
            or os.environ.get("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "")
        )

        if mode == "subscribe" and token:
            if expected_token:
                if hmac.compare_digest(token, expected_token):
                    return HttpResponse(challenge, content_type="text/plain", status=200)
            elif not is_production:
                # In non-production only, if no verify token is explicitly configured, accept dev fallback
                if token == "gqt-hrms-wa-verify":
                    return HttpResponse(challenge, content_type="text/plain", status=200)

        return HttpResponse("Verification failed", content_type="text/plain", status=403)

    def post(self, request: Request) -> Response:
        """Handle incoming delivery status callbacks idempotently with fail-closed authentication."""
        import os
        from django.conf import settings
        from django.utils import timezone
        from apps.crm.adapters.whatsapp import get_whatsapp_adapter

        adapter = get_whatsapp_adapter()
        is_production = (
            getattr(settings, "ENVIRONMENT", "").lower() == "production"
            or not getattr(settings, "DEBUG", True)
        )
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        app_secret = (
            getattr(settings, "WHATSAPP_WEBHOOK_APP_SECRET", "")
            or os.environ.get("WHATSAPP_WEBHOOK_APP_SECRET", "")
            or os.environ.get("WHATSAPP_API_SECRET", "")
        )

        # 1. In production, configured application secret is strictly mandatory
        if is_production and not app_secret:
            logger.error("[WHATSAPP_WEBHOOK_AUTH_FAILED] Missing WHATSAPP_WEBHOOK_APP_SECRET in production.")
            return Response(
                {"error": "Webhook authentication misconfigured in production."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. When app_secret is configured, signature verification must fail closed
        if app_secret:
            if not sig_header:
                return Response(
                    {"error": "Missing signature header (X-Hub-Signature-256)."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            if not adapter.verify_webhook_signature(request.body, sig_header, app_secret):
                return Response(
                    {"error": "Invalid signature."},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

        # 3. Only mutate records after authentication succeeds
        data = request.data or {}
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                statuses = value.get("statuses", [])
                for st in statuses:
                    msg_id = st.get("id")
                    st_val = st.get("status")
                    if msg_id:
                        reminder = FollowUpReminderItem.objects.filter(provider_message_id=msg_id).first()
                        if reminder:
                            if st_val in ["delivered", "read"]:
                                reminder.status = "DELIVERED"
                                reminder.delivered_at = timezone.now()
                                reminder.save(update_fields=["status", "delivered_at", "updated_at"])
                            elif st_val == "failed":
                                reminder.status = "FAILED"
                                reminder.error_message = f"Webhook reported failure: {st.get('errors')}"
                                reminder.save(update_fields=["status", "error_message", "updated_at"])

        return Response({"status": "received"}, status=status.HTTP_200_OK)

