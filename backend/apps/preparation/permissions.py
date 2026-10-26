"""Role-Based and Object-Level Permissions for Student Preparation (Phase 6)."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog


STAFF_PREPARATION_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.TRAINER,
}

EVALUATOR_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.TRAINER,
    RoleCatalog.EVALUATOR,
}

PLACEMENT_HEAD_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
}


class IsTrainerOrStaff(permissions.BasePermission):
    """Allows access to Placement Trainers, Placement Officers, Placement Heads, and Admins."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & STAFF_PREPARATION_ROLES or request.user.is_staff or request.user.is_superuser)


class IsEvaluatorOrStaff(permissions.BasePermission):
    """Allows access to Mock Interview Evaluators and Preparation Staff."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & EVALUATOR_ROLES or request.user.is_staff or request.user.is_superuser)


class CanCertifyPlacementReadiness(permissions.BasePermission):
    """Strict authorization gate: only Placement Head or Administrator can certify placement readiness (Step 23)."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        return bool(user_roles & PLACEMENT_HEAD_ROLES or request.user.is_staff or request.user.is_superuser)


class IsStudentOrStaff(permissions.BasePermission):
    """Allows students to view/interact with their own preparation records, while staff have broader access."""

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False

        user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
        if user_roles & EVALUATOR_ROLES or request.user.is_staff or request.user.is_superuser:
            return True

        # Candidate isolation: verify ownership
        student_obj = getattr(obj, "student", None)
        if student_obj and hasattr(student_obj, "user"):
            return student_obj.user == request.user

        return False
