"""Role-Based and Object-Level Permissions for Candidate Submissions & Profile Dispatch (Phase 7)."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog

SUBMISSION_MANAGEMENT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
}

ACKNOWLEDGEMENT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
}

AUDIT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
    RoleCatalog.AUDITOR,
}


class CanManageSubmissions(permissions.BasePermission):
    """Allows Placement Officers, Placement Heads, and Administrators to manage submission packages."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & SUBMISSION_MANAGEMENT_ROLES or request.user.is_staff or request.user.is_superuser)


class CanAcknowledgeSubmissions(permissions.BasePermission):
    """Allows Placement Staff and HR Relationship Managers to record company acknowledgements."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & ACKNOWLEDGEMENT_ROLES or request.user.is_staff or request.user.is_superuser)


class IsStudentOrStaffSubmissionAccess(permissions.BasePermission):
    """Allows students to view their own submission records, and placement staff full access."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if user_roles & AUDIT_ROLES or request.user.is_staff or request.user.is_superuser:
            return True

        # Candidate isolation: verify student ownership
        student_obj = getattr(obj, "student", None)
        if student_obj and hasattr(student_obj, "user"):
            return student_obj.user == request.user

        return False
