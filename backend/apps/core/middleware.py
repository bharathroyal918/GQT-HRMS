"""HTTP Middleware for request tracing, correlation ID, and security boundaries."""
import uuid
from typing import Callable
from django.http import HttpRequest, HttpResponse
from apps.core.logging import set_current_correlation_id, clear_current_correlation_id


class CorrelationIdMiddleware:
    """Extracts or generates an X-Correlation-ID for every incoming HTTP request.

    - Propagates ID into request.correlation_id
    - Propagates ID into thread-local logging context
    - Returns X-Correlation-ID in response headers for client-side tracing
    """

    HEADER_NAME = "HTTP_X_CORRELATION_ID"
    RESPONSE_HEADER = "X-Correlation-ID"

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        correlation_id = request.META.get(self.HEADER_NAME)

        # Validate or generate new UUIDv4
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        else:
            # Basic sanitization to prevent header injection
            correlation_id = correlation_id[:64].strip()

        request.correlation_id = correlation_id
        set_current_correlation_id(correlation_id)

        try:
            response = self.get_response(request)
            response[self.RESPONSE_HEADER] = correlation_id
            return response
        finally:
            clear_current_correlation_id()
