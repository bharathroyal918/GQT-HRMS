"""URL routing for Job Requirements & Verification Checklist (Phase 3)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.jobs.views import JobRequirementViewSet

app_name = "jobs"

router = DefaultRouter()
router.register(r"requirements", JobRequirementViewSet, basename="requirement")

urlpatterns = [
    path("", include(router.urls)),
]
