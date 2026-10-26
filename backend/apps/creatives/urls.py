"""URL routing for Creative Studio & Promotional Assets (Phase 4)."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.creatives.views import CreativeRequestViewSet

app_name = "creatives"

router = DefaultRouter()
router.register(r"requests", CreativeRequestViewSet, basename="request")

urlpatterns = [
    path("", include(router.urls)),
]
