"""Root URL Configuration for GQT HRMS & Recruitment CRM Platform.

Versioned API Namespace: /api/v1/
OpenAPI 3.1 Documentation: /api/v1/schema/swagger/ and /api/v1/schema/redoc/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Versioned API Namespace: /api/v1/
    path(
        "api/v1/",
        include(
            [
                # Core Infrastructure & Diagnostics
                path("", include("apps.core.urls", namespace="core")),

                # Identity, Authentication & RBAC
                path("auth/", include("apps.accounts.urls")),

                # Corporate CRM & HR Directory
                path("crm/", include("apps.crm.urls")),

                # Job Requirements & Verification Checklist (Phase 3)
                path("jobs/", include("apps.jobs.urls")),

                # Creative Studio & Promotional Assets (Phase 4)
                path("creatives/", include("apps.creatives.urls")),

                # Students & Eligibility Engine (Phase 5)
                path("students/", include("apps.students.urls")),

                # Student Preparation (Phase 6 / Steps 15-23)
                path("preparation/", include("apps.preparation.urls")),

                # Candidate Submissions & Profile Dispatch (Phase 7 / Steps 24-28)
                path("submissions/", include("apps.submissions.urls")),

                # Interview Management & Tracking (Phase 8 / Steps 29-35)
                path("interviews/", include("apps.interviews.urls")),

                # Placement Management & Tracking (Phase 8 / Steps 36-41)
                path("placements/", include("apps.placements.urls")),

                # OpenAPI 3.1 Documentation
                path("schema/", SpectacularAPIView.as_view(), name="schema"),
                path(
                    "schema/swagger/",
                    SpectacularSwaggerView.as_view(url_name="schema"),
                    name="swagger-ui",
                ),
                path(
                    "schema/redoc/",
                    SpectacularRedocView.as_view(url_name="schema"),
                    name="redoc",
                ),
            ]
        ),
    ),
]

handler404 = "apps.core.views.custom_404_view"
handler500 = "apps.core.views.custom_500_view"
