"""Base RBAC permission classes."""
from typing import Sequence
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class AllowAnyReadOnly(BasePermission):
    """Allows unauthenticated access for safe HTTP methods (GET, HEAD, OPTIONS)."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        return request.method in ("GET", "HEAD", "OPTIONS")


class HasRole(BasePermission):
    """Dynamic permission verifying that the authenticated user possesses at least one allowed role."""

    allowed_roles: Sequence[str] = ()

    def __init__(self, allowed_roles: Sequence[str] = ()):
        if allowed_roles:
            self.allowed_roles = allowed_roles

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_superuser:
            return True

        if hasattr(request.user, "get_role_codes"):
            user_roles = request.user.get_role_codes()
            return any(role in user_roles for role in self.allowed_roles)

        return False
