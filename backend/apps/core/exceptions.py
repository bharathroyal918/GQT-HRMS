"""Standardized DRF Exception Handler and Error Envelopes."""
from typing import Any, Dict, Optional
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from apps.core.logging import get_current_correlation_id


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Optional[Response]:
    """Intercept DRF exceptions and wrap them in a consistent JSON error envelope."""
    response = exception_handler(exc, context)
    correlation_id = get_current_correlation_id()

    if response is None:
        # Unhandled 500 server error
        return Response(
            {
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected server error occurred. Please contact system support.",
                    "details": {},
                    "correlation_id": correlation_id,
                },
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Standardize error codes based on status code
    code_map = {
        status.HTTP_400_BAD_REQUEST: "VALIDATION_FAILED",
        status.HTTP_401_UNAUTHORIZED: "AUTHENTICATION_REQUIRED",
        status.HTTP_403_FORBIDDEN: "PERMISSION_DENIED",
        status.HTTP_404_NOT_FOUND: "RESOURCE_NOT_FOUND",
        status.HTTP_405_METHOD_NOT_ALLOWED: "METHOD_NOT_ALLOWED",
        status.HTTP_429_TOO_MANY_REQUESTS: "RATE_LIMIT_EXCEEDED",
    }
    error_code = code_map.get(response.status_code, "API_ERROR")

    # Format message and details cleanly
    message = "Request processing failed."
    details = response.data

    if isinstance(response.data, dict):
        if "detail" in response.data:
            message = str(response.data["detail"])
            details = {k: v for k, v in response.data.items() if k != "detail"}
    elif isinstance(response.data, list):
        message = "; ".join(str(item) for item in response.data)

    response.data = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "details": details,
            "correlation_id": correlation_id,
        },
    }
    return response
