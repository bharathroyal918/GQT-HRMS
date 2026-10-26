"""Rate limiting and throttling classes for authentication endpoints."""
from rest_framework.throttling import ScopedRateThrottle


class AuthRateThrottle(ScopedRateThrottle):
    """Rate limit specifically applied to login and password recovery operations."""

    scope = "auth"
