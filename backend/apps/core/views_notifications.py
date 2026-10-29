"""API Views for Global Notification Center (Phase 15 Workstream 3).

Exposes list, retrieve, unread-count, mark-read, and mark-all-read operations.
Enforces that business logic resides in Selectors and Services.
"""
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.pagination import StandardResultsSetPagination
from apps.core.selectors_notifications import (
    get_unread_notification_count,
    get_user_notifications,
)
from apps.core.serializers_notifications import (
    NotificationSerializer,
    NotificationUnreadCountSerializer,
)
from apps.core.services_notifications import (
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


@extend_schema_view(
    list=extend_schema(summary="List in-app notifications for authenticated user"),
    retrieve=extend_schema(summary="Retrieve an in-app notification by ID"),
)
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """Authenticated user notification center endpoints."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    serializer_class = NotificationSerializer

    def get_queryset(self):
        params = self.request.query_params
        is_read_param = params.get("is_read")
        is_read = None
        if is_read_param is not None:
            is_read = is_read_param.lower() in ("true", "1", "yes")

        category = params.get("category")
        return get_user_notifications(
            user=self.request.user,
            is_read=is_read,
            category=category,
        )

    @extend_schema(summary="Get unread notification count for badge", responses={200: NotificationUnreadCountSerializer})
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request: Request) -> Response:
        count = get_unread_notification_count(request.user)
        return Response({"success": True, "count": count})

    @extend_schema(summary="Mark notification as read", responses={200: NotificationSerializer})
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request: Request, pk=None) -> Response:
        notification = mark_notification_as_read(request.user, pk)
        return Response({"success": True, "data": NotificationSerializer(notification).data})

    @extend_schema(summary="Mark all unread notifications as read")
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request: Request) -> Response:
        count = mark_all_notifications_as_read(request.user)
        return Response({
            "success": True,
            "count": count,
            "message": f"Successfully marked {count} notifications as read.",
        })

