"""Permissions for Reports & Analytics (Phase 11).

Enforces strict role-based access control (RBAC) and data isolation:
- Full Access: ADMIN, PLACEMENT_HEAD, PLACEMENT_OFFICER
- Read-Only Access: AUDITOR (safe read-only)
- Scoped Corporate Access: HR_RELATIONSHIP_MGR
- Academic Aggregates: TRAINER, EVALUATOR
- Student Isolation: STUDENT role is strictly barred from all organizational aggregates
  and can only access their personal report summary.
"""
from rest_framework.permissions import BasePermission
from apps.accounts.models import RoleCatalog


STAFF_ROLES = {
    RoleCatalog.ADMIN,
    RoleCatalog.PLACEMENT_HEAD,
    RoleCatalog.PLACEMENT_OFFICER,
}

AUDITOR_ROLES = {
    RoleCatalog.AUDITOR,
}

HR_MGR_ROLES = {
    RoleCatalog.HR_RELATIONSHIP_MGR,
}

ACADEMIC_EVAL_ROLES = {
    RoleCatalog.TRAINER,
    RoleCatalog.EVALUATOR,
}


def get_user_roles(user) -> set:
    """Extract active role codes safely for user."""
    if not user or not user.is_authenticated:
        return set()
    if getattr(user, "is_superuser", False):
        return {RoleCatalog.ADMIN}
    if hasattr(user, "get_active_roles"):
        return set(user.get_active_roles())
    return set(user.role_assignments.filter(is_active=True).values_list("role__code", flat=True))


class CanAccessCompanyReports(BasePermission):
    """Staff, HR Managers, and Auditors may access Company Reports."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        allowed = STAFF_ROLES | AUDITOR_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessStudentReports(BasePermission):
    """Staff, Trainers, Evaluators, and Auditors may access Student Reports. Students strictly denied."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        # Students are strictly denied aggregate student reports
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES)):
            return False
        allowed = STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES
        return bool(roles & allowed)


class CanAccessPlacementReports(BasePermission):
    """Staff, HR Managers, and Auditors may access Placement Reports."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        allowed = STAFF_ROLES | AUDITOR_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessPerformanceReports(BasePermission):
    """Staff, Evaluators, Trainers, HR Managers, and Auditors may access Conversion Funnel Reports."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        allowed = STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessMonthlyStatistics(BasePermission):
    """Staff, HR Managers, and Auditors may access Monthly Statistics."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        allowed = STAFF_ROLES | AUDITOR_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessStudentSelfReport(BasePermission):
    """Students may access their own personal report summary, as well as staff and auditors."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        allowed = STAFF_ROLES | AUDITOR_ROLES | {RoleCatalog.STUDENT}
        return bool(roles & allowed)


# =========================================================================
# Phase 13: Continuous Improvement Permissions
# =========================================================================
class CanAccessPlacementRateAnalytics(BasePermission):
    """Staff, HR Managers, and Auditors may access granular placement analytics. Students strictly denied."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES | HR_MGR_ROLES)):
            return False
        allowed = STAFF_ROLES | AUDITOR_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessFeedbackIntelligence(BasePermission):
    """Staff, Evaluators, Trainers, HR Managers, and Auditors may access Feedback Intelligence. Students strictly denied."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES | HR_MGR_ROLES)):
            return False
        allowed = STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES | HR_MGR_ROLES
        return bool(roles & allowed)


class CanAccessSkillGapMatrix(BasePermission):
    """Staff, Trainers, Evaluators, and Auditors may access the Skill Gap Matrix. Students strictly denied."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES)):
            return False
        allowed = STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES
        return bool(roles & allowed)


class CanManageTrainingPlans(BasePermission):
    """Staff, Trainers, and Auditors can view training plans; Staff & Trainers can create; Staff can update status."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES)):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            allowed = STAFF_ROLES | AUDITOR_ROLES | ACADEMIC_EVAL_ROLES
            return bool(roles & allowed)
        # Create / Update
        allowed_write = STAFF_ROLES | ACADEMIC_EVAL_ROLES
        return bool(roles & allowed_write)


class CanManageCycleReviews(BasePermission):
    """Staff and Auditors can view cycle reviews; Only Staff can create or modify cycle reviews."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        roles = get_user_roles(request.user)
        if RoleCatalog.STUDENT in roles and not (roles & (STAFF_ROLES | AUDITOR_ROLES)):
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            allowed = STAFF_ROLES | AUDITOR_ROLES
            return bool(roles & allowed)
        return bool(roles & STAFF_ROLES)

