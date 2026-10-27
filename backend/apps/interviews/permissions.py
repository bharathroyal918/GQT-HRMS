"""Role-Based and Object-Level Permissions for Interview Management & Tracking (Phase 8 / Steps 29-35)."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog

INTERVIEW_MANAGEMENT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
}

EVALUATION_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.EVALUATOR,
    RoleCatalog.TRAINER,
}

AUDIT_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
    RoleCatalog.AUDITOR,
}


class CanManageInterviews(permissions.BasePermission):
    """Allows Placement Officers, Placement Heads, CRM Managers, and Admins to manage interviews."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & INTERVIEW_MANAGEMENT_ROLES or request.user.is_staff or request.user.is_superuser)


class CanManageInterviewRounds(permissions.BasePermission):
    """Allows Placement Staff and Evaluators to create and evaluate interview rounds."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & EVALUATION_ROLES or request.user.is_staff or request.user.is_superuser)


class IsStudentOrStaffInterviewAccess(permissions.BasePermission):
    """Allows students to view their own interview records and self-confirm attendance, staff full access."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if user_roles & AUDIT_ROLES or request.user.is_staff or request.user.is_superuser:
            return True

        # Check student ownership
        student_profile = getattr(request.user, "student_profile", None)
        if not student_profile:
            return False

        # If obj is InterviewSchedule
        if hasattr(obj, "student_id"):
            return str(obj.student_id) == str(student_profile.id)

        # If obj is ShortlistedCandidate
        if hasattr(obj, "student"):
            return str(obj.student_id) == str(student_profile.id)

        # If obj is InterviewRound
        if hasattr(obj, "candidate"):
            return str(obj.candidate.student_id) == str(student_profile.id)

        return False
