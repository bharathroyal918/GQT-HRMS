"""URL routing for Global Notification Center (Phase 15 Workstream 3)."""
from rest_framework.routers import DefaultRouter
from apps.core.views_notifications import NotificationViewSet

router = DefaultRouter()
router.register(r"", NotificationViewSet, basename="notification")

urlpatterns = router.urls

