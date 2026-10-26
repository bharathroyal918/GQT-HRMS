"""URL configuration for apps.crm."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.crm.views import (
    CRMConfigurationView,
    CRMDashboardMetricsView,
    CompanyViewSet,
    FollowUpViewSet,
    HRContactViewSet,
    OutreachLogViewSet,
)

app_name = "crm"

router = DefaultRouter()
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"contacts", HRContactViewSet, basename="contact")
router.register(r"outreach", OutreachLogViewSet, basename="outreach")
router.register(r"follow-ups", FollowUpViewSet, basename="follow-up")

urlpatterns = [
    path("dashboard/metrics/", CRMDashboardMetricsView.as_view(), name="dashboard-metrics"),
    path("config/", CRMConfigurationView.as_view(), name="configuration"),
    path("", include(router.urls)),
]
