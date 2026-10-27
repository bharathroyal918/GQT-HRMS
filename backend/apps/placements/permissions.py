"""Role-Based Access Control and Object-Level Permissions for Placement Management."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog

PLACEMENT_STAFF_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
}

OFFER_MANAGEMENT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
}

AUDIT_ROLES = PLACEMENT_STAFF_ROLES | {RoleCatalog.AUDITOR}


class CanManagePlacements(permissions.BasePermission):
    """Allows operations only to authorized placement staff and system administrators."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & PLACEMENT_STAFF_ROLES)


class CanManageOfferLetters(permissions.BasePermission):
    """Allows uploading and replacing offer letters only to placement officers, head, and admin."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & OFFER_MANAGEMENT_ROLES)


class IsStudentOrStaffPlacementAccess(permissions.BasePermission):
    """Allows placement staff full view, and restricts students to their own placement and offer records."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if user_roles & AUDIT_ROLES or request.user.is_staff:
            return True

        # CandidatePlacementStatus object check
        if hasattr(obj, "student") and hasattr(obj.student, "user"):
            return obj.student.user == request.user

        # CandidateOfferLetter object check
        if hasattr(obj, "student") and hasattr(obj.student, "user"):
            return obj.student.user == request.user

        return False
