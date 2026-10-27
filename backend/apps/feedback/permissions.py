"""Role-Based Access Control and Object-Level Permissions for Feedback Collection."""
from rest_framework import permissions
from apps.accounts.models import RoleCatalog

STAFF_VIEW_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.AUDITOR,
}

HR_FEEDBACK_MANAGE_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.HR_RELATIONSHIP_MGR,
}

TRAINER_FEEDBACK_MANAGE_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
    RoleCatalog.TRAINER,
    RoleCatalog.EVALUATOR,
}


def get_user_roles(user) -> set[str]:
    """Helper to extract active assigned role codes for a user."""
    if not user or not user.is_authenticated:
        return set()
    return set(user.role_assignments.filter(is_active=True).values_list("role__code", flat=True))


class IsStudentOrStaffForStudentFeedback(permissions.BasePermission):
    """Allows students to submit and view their own feedback; placement staff and auditors have read access."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        roles = get_user_roles(request.user)
        if request.method in permissions.SAFE_METHODS:
            return bool(roles & (STAFF_VIEW_ROLES | {RoleCatalog.STUDENT}))
        # Writes (POST)
        return bool(roles & {RoleCatalog.STUDENT, RoleCatalog.ADMIN})

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        roles = get_user_roles(request.user)
        # Read operations
        if request.method in permissions.SAFE_METHODS:
            if obj.student.user == request.user:
                return True
            return bool(roles & STAFF_VIEW_ROLES)
        # Update / delete
        if obj.student.user == request.user:
            return True
        return bool(roles & {RoleCatalog.ADMIN})


class CanManageHRFeedback(permissions.BasePermission):
    """Allows HR relationship managers and placement staff to manage HR feedback; auditors read-only."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        roles = get_user_roles(request.user)
        if request.method in permissions.SAFE_METHODS:
            return bool(roles & (HR_FEEDBACK_MANAGE_ROLES | {RoleCatalog.AUDITOR}))
        # Write operations
        return bool(roles & HR_FEEDBACK_MANAGE_ROLES)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        roles = get_user_roles(request.user)
        if request.method in permissions.SAFE_METHODS:
            return bool(roles & (HR_FEEDBACK_MANAGE_ROLES | {RoleCatalog.AUDITOR}))
        # Auditor cannot write
        if RoleCatalog.AUDITOR in roles and not bool(roles & HR_FEEDBACK_MANAGE_ROLES):
            return False
        return bool(roles & HR_FEEDBACK_MANAGE_ROLES)


class CanManageTrainerFeedback(permissions.BasePermission):
    """Allows trainers and evaluators to submit feedback; placement staff supervisory access."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        roles = get_user_roles(request.user)
        if request.method in permissions.SAFE_METHODS:
            return bool(roles & (TRAINER_FEEDBACK_MANAGE_ROLES | {RoleCatalog.AUDITOR}))
        return bool(roles & TRAINER_FEEDBACK_MANAGE_ROLES)

    def has_object_permission(self, request, view, obj) -> bool:
        if request.user.is_superuser:
            return True
        roles = get_user_roles(request.user)
        if request.method in permissions.SAFE_METHODS:
            if obj.trainer == request.user:
                return True
            return bool(roles & (STAFF_VIEW_ROLES | {RoleCatalog.TRAINER, RoleCatalog.EVALUATOR}))
        # Write operations: only original trainer or Admin
        if obj.trainer == request.user or bool(roles & {RoleCatalog.ADMIN}):
            return True
        return False


class CanViewFeedbackSummary(permissions.BasePermission):
    """Controls access to aggregated feedback KPIs and summaries."""

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        roles = get_user_roles(request.user)
        # Deny students from viewing staff-wide summary dashboards
        return bool(roles & (STAFF_VIEW_ROLES | HR_FEEDBACK_MANAGE_ROLES | TRAINER_FEEDBACK_MANAGE_ROLES))
