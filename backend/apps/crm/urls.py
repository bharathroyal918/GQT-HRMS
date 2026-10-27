"""URL configuration for apps.crm."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.crm.views import (
    CaseEscalationViewSet,
    CRMAutomationRunView,
    CRMConfigurationView,
    CRMDashboardMetricsView,
    CRMReconciliationDiagnosticsView,
    CRMReconciliationHistoryView,
    CRMReconciliationSyncView,
    CompanyViewSet,
    FollowUpViewSet,
    HRContactViewSet,
    OutreachLogViewSet,
    StaffNotificationViewSet,
    Student360View,
    StudentTimelineView,
    WhatsAppWebhookView,
)

app_name = "crm"

router = DefaultRouter()
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"contacts", HRContactViewSet, basename="contact")
router.register(r"outreach", OutreachLogViewSet, basename="outreach")
router.register(r"follow-ups", FollowUpViewSet, basename="follow-up")
router.register(r"escalations", CaseEscalationViewSet, basename="case-escalation")
router.register(r"notifications", StaffNotificationViewSet, basename="staff-notification")

urlpatterns = [
    path("dashboard/metrics/", CRMDashboardMetricsView.as_view(), name="dashboard-metrics"),
    path("config/", CRMConfigurationView.as_view(), name="configuration"),
    path("automation/run/", CRMAutomationRunView.as_view(), name="automation-run"),
    path("webhooks/whatsapp/", WhatsAppWebhookView.as_view(), name="webhook-whatsapp"),
    path("reconciliation/diagnostics/", CRMReconciliationDiagnosticsView.as_view(), name="reconciliation-diagnostics"),
    path("reconciliation/sync/", CRMReconciliationSyncView.as_view(), name="reconciliation-sync"),
    path("reconciliation/history/", CRMReconciliationHistoryView.as_view(), name="reconciliation-history"),
    path("students/<str:student_id>/360/", Student360View.as_view(), name="student-360"),
    path("students/<str:student_id>/timeline/", StudentTimelineView.as_view(), name="student-timeline"),
    path("", include(router.urls)),
]

