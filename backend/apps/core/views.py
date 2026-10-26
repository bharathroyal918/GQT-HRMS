"""Diagnostic and health check views for GQT HRMS API."""
import logging
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from apps.core.logging import get_current_correlation_id
from apps.core.serializers import (
    HealthCheckResponseSerializer,
    ReadinessCheckResponseSerializer,
)

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Public liveness probe verifying that the application process is running.

    Strict Security Invariant: Zero secrets, internal IPs, or database URLs are disclosed.
    """

    permission_classes = [AllowAny]
    throttle_scope = "health"

    @extend_schema(
        summary="Liveness Health Check",
        description="Returns basic application status for load balancer liveness probes.",
        responses={200: HealthCheckResponseSerializer},
        tags=["System Diagnostics"],
    )
    def get(self, request, *args, **kwargs) -> Response:
        payload = {
            "status": "UP",
            "service": "gqt-hrms-api",
            "version": "1.0.0",
            "environment": getattr(settings, "ENVIRONMENT", "development"),
            "timestamp": timezone.now(),
            "correlation_id": get_current_correlation_id(),
        }
        return Response(payload, status=status.HTTP_200_OK)


class ReadinessCheckView(APIView):
    """Readiness probe validating database connectivity and media storage accessibility."""

    permission_classes = [AllowAny]
    throttle_scope = "health"

    @extend_schema(
        summary="Infrastructure Readiness Probe",
        description="Verifies database execution and storage readiness before receiving production traffic.",
        responses={
            200: ReadinessCheckResponseSerializer,
            503: ReadinessCheckResponseSerializer,
        },
        tags=["System Diagnostics"],
    )
    def get(self, request, *args, **kwargs) -> Response:
        correlation_id = get_current_correlation_id()
        is_ready = True
        db_status = "UP"
        storage_status = "UP"

        # Probe Database Connectivity (safe execution without data exposure)
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                row = cursor.fetchone()
                if not row or row[0] != 1:
                    db_status = "DOWN"
                    is_ready = False
        except Exception as exc:
            logger.error("Readiness check database probe failed: %s", str(exc))
            db_status = "DOWN"
            is_ready = False

        # Probe Media Root access
        try:
            media_path = getattr(settings, "MEDIA_ROOT", None)
            if media_path and not media_path.exists():
                media_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.error("Readiness check storage probe failed: %s", str(exc))
            storage_status = "DOWN"
            is_ready = False

        http_status = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
        payload = {
            "status": "READY" if is_ready else "NOT_READY",
            "database": {"status": db_status},
            "storage": {"status": storage_status},
            "timestamp": timezone.now(),
            "correlation_id": correlation_id,
        }
        return Response(payload, status=http_status)


def custom_404_view(request, exception=None) -> JsonResponse:
    """Fallback handler for unmapped URLs returning standardized JSON."""
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "RESOURCE_NOT_FOUND",
                "message": "The requested endpoint does not exist on this server.",
                "details": {"path": request.path},
                "correlation_id": get_current_correlation_id(),
            },
        },
        status=404,
    )


def custom_500_view(request) -> JsonResponse:
    """Fallback handler for unhandled server exceptions returning standardized JSON."""
    return JsonResponse(
        {
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred.",
                "details": {},
                "correlation_id": get_current_correlation_id(),
            },
        },
        status=500,
    )
