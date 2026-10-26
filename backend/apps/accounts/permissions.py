"""Permission classes for Role-Based Access Control and Object-Level Authorization."""
from typing import Sequence, Type
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView
from apps.accounts.models import RoleCatalog


class IsAdminOrSuperUser(permissions.BasePermission):
    """Allows access only to Superusers and Users holding the active ADMIN role."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        return request.user.is_superuser or request.user.has_role(RoleCatalog.ADMIN)


def role_required(*allowed_roles: str) -> Type[permissions.BasePermission]:
    """Factory creating a DRF Permission class that enforces active possession of any of the specified roles."""

    class DynamicRolePermission(permissions.BasePermission):
        def has_permission(self, request: Request, view: APIView) -> bool:
            if not (request.user and request.user.is_authenticated and request.user.is_active):
                return False
            if request.user.is_superuser or request.user.has_role(RoleCatalog.ADMIN):
                return True
            return request.user.has_any_role(*allowed_roles)

    DynamicRolePermission.__name__ = f"RoleRequired_{'_'.join(allowed_roles)}"
    return DynamicRolePermission


class IsPlacementHead(permissions.BasePermission):
    """Allows access to Placement Head or Admin for internal sign-offs and approvals."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        return (
            request.user.is_superuser
            or request.user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
        )


class IsPlacementOfficerOrHead(permissions.BasePermission):
    """Allows access to Placement Officers, Placement Heads, and Admins."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        return (
            request.user.is_superuser
            or request.user.has_any_role(
                RoleCatalog.ADMIN,
                RoleCatalog.PLACEMENT_HEAD,
                RoleCatalog.PLACEMENT_OFFICER,
            )
        )


class IsSelfOrAdmin(permissions.BasePermission):
    """Object-level permission allowing users to manage only their own record, unless Admin."""

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.is_superuser or request.user.has_role(RoleCatalog.ADMIN):
            return True
        return obj == request.user or getattr(obj, "user", None) == request.user
