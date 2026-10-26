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
