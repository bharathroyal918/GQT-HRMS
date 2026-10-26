"""Role-Based and Object-Level Permissions for Student & Eligibility Workflows."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog


STAFF_ROLES = [
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
]

AUDIT_ROLES = STAFF_ROLES + [RoleCatalog.AUDITOR]


class CanPublishJobNotification(permissions.BasePermission):
    """Allow only Placement Officers, Placement Heads, or Admins to broadcast job notices."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = request.user.get_active_roles()
        return any(role in STAFF_ROLES for role in user_roles)


class CanOverrideEligibility(permissions.BasePermission):
    """Allow Placement Officers, Placement Heads, or Admins to manually override candidate eligibility."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = request.user.get_active_roles()
        return any(role in STAFF_ROLES for role in user_roles)


class CanFinalizeCohort(permissions.BasePermission):
    """Strictly gate cohort finalization to Placement Heads and Admins only."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = request.user.get_active_roles()
        return any(role in [RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD] for role in user_roles)


class CanViewCohort(permissions.BasePermission):
    """Allow placement staff and auditors to view candidate cohorts."""

    def has_permission(self, request, view) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        user_roles = request.user.get_active_roles()
        return any(role in AUDIT_ROLES for role in user_roles)


class IsStudentOwnerOrStaff(permissions.BasePermission):
    """Object-level permission ensuring students can only access their own profile, resumes, and applications."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True

        user_roles = request.user.get_active_roles()
        if any(role in AUDIT_ROLES for role in user_roles):
            return True

        # Check ownership depending on target object type
        if hasattr(obj, "user"):
            return obj.user == request.user
        if hasattr(obj, "student"):
            return obj.student.user == request.user
        return False
